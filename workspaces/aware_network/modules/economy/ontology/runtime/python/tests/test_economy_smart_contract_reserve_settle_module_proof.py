from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.wallet_custody import derive_wallet_custody_material
from aware_history.stable_ids import stable_portal_branch_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.invocation_engine import (
    MetaGraphCallTarget,
    MetaGraphCommitReceipt,
    MetaGraphInvokeFunctionInput,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    ROOT_OBJECT_ID,
    SourceObjectId,
    run_meta_runtime_proof,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)


ECONOMY_COIN_CLASS_FQN = "aware_economy.coin.Coin"
ECONOMY_ESCROW_CLASS_FQN = "aware_economy.escrow.Escrow"
ECONOMY_FINANCE_ENTITY_CLASS_FQN = "aware_economy.finance.FinanceEntity"
ECONOMY_PRICE_CLASS_FQN = "aware_economy.price.Price"
ECONOMY_PRICE_SCHEDULE_CLASS_FQN = "aware_economy.price.PriceSchedule"
ECONOMY_PRICING_POLICY_CLASS_FQN = "aware_economy.price.PricingPolicy"
ECONOMY_SMART_CONTRACT_CLASS_FQN = "aware_economy.smart_contract.SmartContract"
ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN = "aware_economy.smart_contract.SmartContractConfig"
ECONOMY_WALLET_CLASS_FQN = "aware_economy.wallet.Wallet"

_ECONOMY_META_HANDLERS_ANY: Any = economy_meta_handlers
_ECONOMY_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _ECONOMY_META_HANDLERS_ANY,
)
_ECONOMY_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _ECONOMY_META_HANDLERS_ANY,
)


def _build_economy_meta_runtime(
    *,
    repo_root: Path,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=economy_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(_ECONOMY_META_HANDLER_MODULE,),
        bootstrap_modules=(_ECONOMY_META_BOOTSTRAP_MODULE,),
    )
    assert runtime.context is not None
    return runtime


def _custody_wallet_inputs(*, identity_id: UUID) -> tuple[str, str, str]:
    custody = derive_wallet_custody_material(
        identity_id=identity_id,
        role_key="primary",
    )
    return custody.address, custody.public_key, custody.private_key_encrypted


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


def _expect_enum_value(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: str,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert getattr(value, "value", value) == expected


async def _assert_failed_no_commit(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    projection_hash: str,
    object_id: UUID | SourceObjectId,
    class_fqn: str,
    function_name: str,
    args: Sequence[object],
    error_fragment: str,
) -> None:
    assert lane.branch_id is not None
    store = FSCommitStore()
    head_before = await store.head(
        branch_id=lane.branch_id,
        projection_hash=projection_hash,
    )

    try:
        response = await _invoke_instance(
            runtime=runtime,
            lane=lane,
            projection_hash=projection_hash,
            object_id=object_id,
            class_fqn=class_fqn,
            function_name=function_name,
            args=args,
        )
    except Exception as exc:
        failure_text = str(exc)
    else:
        assert response.status == "failed"
        failure_text = response.error or "\n".join(response.logs)
        assert response.commit_id is None
    assert error_fragment in failure_text

    head_after = await store.head(
        branch_id=lane.branch_id,
        projection_hash=projection_hash,
    )
    assert head_after == head_before


async def _invoke_instance(
    *,
    runtime: MetaGraphRuntime,
    lane: LaneIds,
    projection_hash: str,
    object_id: UUID | SourceObjectId,
    class_fqn: str,
    function_name: str,
    args: Sequence[object] = (),
    kwargs: dict[str, object] | None = None,
) -> MetaGraphCommitReceipt:
    if lane.branch_id is None:
        raise AssertionError("Direct Meta instance invocation requires branch_id")
    context = runtime.context
    if context is None:
        raise AssertionError("Direct Meta instance invocation requires runtime context")
    index = context.index
    function_config = _resolve_function_config(
        index=index,
        class_fqn=class_fqn,
        function_name=function_name,
    )
    if isinstance(object_id, SourceObjectId):
        target_object_id = await _resolve_lane_class_instance_id_for_source_object(
            index=index,
            branch_id=lane.branch_id,
            projection_hash=projection_hash,
            source_object_id=object_id.value,
        )
    else:
        target_object_id = object_id

    return await runtime.invoke_function(
        MetaGraphInvokeFunctionInput(
            index=index,
            actor_id=lane.actor_id or META_SYSTEM_ACTOR_ID,
            function_id=function_config.id,
            domain_branch_id=lane.branch_id,
            domain_projection_hash=projection_hash,
            call_target=MetaGraphCallTarget.instance,
            target_object_id=target_object_id,
            object_projection_graph_id=None,
            args=JsonArray([_jsonify_value(value) for value in args]),
            kwargs=JsonObject({str(key): _jsonify_value(value) for key, value in (kwargs or {}).items()}),
            commit=True,
            publish=False,
        )
    )


def _resolve_function_config(
    *,
    index: MetaGraphRuntimeIndex,
    class_fqn: str,
    function_name: str,
) -> FunctionConfig:
    matches: list[FunctionConfig] = []
    for class_config in index.class_configs_by_id.values():
        if class_config.class_fqn != class_fqn:
            continue
        for edge in class_config.class_config_function_configs:
            function_config = edge.function_config
            if function_config.name == function_name:
                matches.append(function_config)
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise AssertionError(
            "FunctionConfig not found in Meta graph index: " f"class_fqn={class_fqn!r} function_name={function_name!r}"
        )
    raise AssertionError(
        "FunctionConfig is ambiguous in Meta graph index: "
        f"class_fqn={class_fqn!r} function_name={function_name!r} "
        f"matches={[item.id for item in matches]}"
    )


async def _resolve_lane_class_instance_id_for_source_object(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    source_object_id: UUID,
) -> UUID:
    oig = await _materialize_lane_head(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    for instance in oig.class_instances:
        if instance.source_object_id != source_object_id:
            continue
        if instance.id is None:
            break
        return instance.id
    raise AssertionError(
        "SourceObjectId could not resolve to a class-instance id in the "
        "materialized lane: "
        f"source_object_id={source_object_id} "
        f"branch_id={branch_id} projection_hash={projection_hash}"
    )


async def _materialize_lane_head(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
) -> ObjectInstanceGraph:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if not head or not head.get("commit_id") or not head.get("object_instance_graph_id"):
        raise AssertionError(
            "Direct Meta invocation requires a committed lane head: "
            f"branch_id={branch_id} projection_hash={projection_hash}"
        )
    opg = index.opg_by_hash[projection_hash]
    oig, _ = await OIGMaterializer().get(
        branch_id=branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=UUID(str(head["commit_id"])),
        oig_id=UUID(str(head["object_instance_graph_id"])),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    return oig


def _jsonify_value(value: object) -> JsonValue:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return cast(JsonValue, value)


def _json_datetime(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


@pytest.mark.asyncio
async def test_economy_smart_contract_reserve_then_settle_proof_with_fail_closed_invariants(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_economy_ontology  # noqa: F401
    from aware_economy_ontology.coin.coin_enums import CoinType
    from aware_economy_ontology.price.price_enums import PriceType
    from aware_economy_ontology.smart_contract.smart_contract_enums import (
        SmartContractMemberType,
        SmartContractType,
    )
    from aware_economy_ontology.stable_ids import (
        stable_coin_id,
        stable_escrow_id,
        stable_finance_entity_id,
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
        stable_wallet_private_id,
        stable_wallet_public_id,
    )

    with IsolatedAwareRoot(tmp_path / "aware_root", persistence_backend="fs") as aware_root:
        runtime = _build_economy_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        assert runtime.context is not None
        idx = runtime.context.index
        opgs = {opg.name: opg for opg in idx.opg_by_hash.values()}
        required = {
            "Wallet",
            "FinanceEntity",
            "Coin",
            "Escrow",
            "Price",
            "PricingPolicy",
            "SmartContract",
            "SmartContractConfig",
            "Transaction",
        }
        assert required.issubset(opgs.keys())

        payer_lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )
        receiver_lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )

        payer_identity_id = uuid4()
        receiver_identity_id = uuid4()
        payer_address, payer_public_key, payer_private_key_encrypted = _custody_wallet_inputs(
            identity_id=payer_identity_id
        )
        receiver_address, receiver_public_key, receiver_private_key_encrypted = _custody_wallet_inputs(
            identity_id=receiver_identity_id
        )

        payer_wallet_public_id = stable_wallet_public_id(public_key=payer_public_key)
        _ = stable_wallet_private_id(private_key_encrypted=payer_private_key_encrypted)
        payer_wallet_id = stable_wallet_id(
            public_key=payer_public_key,
            private_key_encrypted=payer_private_key_encrypted,
        )
        payer_finance_entity_id = stable_finance_entity_id(identity_id=payer_identity_id)

        receiver_wallet_public_id = stable_wallet_public_id(public_key=receiver_public_key)
        _ = stable_wallet_private_id(private_key_encrypted=receiver_private_key_encrypted)
        receiver_wallet_id = stable_wallet_id(
            public_key=receiver_public_key,
            private_key_encrypted=receiver_private_key_encrypted,
        )
        receiver_finance_entity_id = stable_finance_entity_id(identity_id=receiver_identity_id)

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=payer_lane,
            opg_name="Wallet",
            root_class_fqn=ECONOMY_WALLET_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        payer_address,
                        payer_public_key,
                        payer_private_key_encrypted,
                    ],
                    expected_root_object_id=payer_wallet_id,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="Wallet",
            root_class_fqn=ECONOMY_WALLET_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        receiver_address,
                        receiver_public_key,
                        receiver_private_key_encrypted,
                    ],
                    expected_root_object_id=receiver_wallet_id,
                )
            ],
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=payer_lane,
            opg_name="FinanceEntity",
            root_class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
                    function_name="build",
                    args=[payer_identity_id, payer_wallet_id],
                    expected_root_object_id=payer_finance_entity_id,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="FinanceEntity",
            root_class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
                    function_name="build",
                    args=[receiver_identity_id, receiver_wallet_id],
                    expected_root_object_id=receiver_finance_entity_id,
                )
            ],
        )

        coin_id = stable_coin_id(symbol="USD")
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="Coin",
            root_class_fqn=ECONOMY_COIN_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_COIN_CLASS_FQN,
                    function_name="build",
                    args=["USD", "US Dollar", CoinType.fiat.value],
                    kwargs={"decimals": 2},
                    expected_root_object_id=coin_id,
                )
            ],
        )

        smart_contract_config_id = stable_smart_contract_config_id(
            name="InferencePayment", type=SmartContractType.utility.value
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="SmartContractConfig",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN,
                    function_name="build",
                    args=[
                        "InferencePayment",
                        "Smart-contract gate for inference settlement",
                        SmartContractType.utility.value,
                    ],
                    expected_root_object_id=smart_contract_config_id,
                )
            ],
        )

        smart_contract_id = stable_smart_contract_id(
            smart_contract_config_id=smart_contract_config_id,
            blockchain_address="dev:inference",
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="SmartContract",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="build_via_smart_contract_config",
                    args=[smart_contract_config_id, "dev:inference"],
                    expected_root_object_id=smart_contract_id,
                )
            ],
        )

        pricing_policy_id = stable_pricing_policy_id(name="default-service-policy", version=1)
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="PricingPolicy",
            root_class_fqn=ECONOMY_PRICING_POLICY_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_PRICING_POLICY_CLASS_FQN,
                    function_name="build",
                    args=["default-service-policy", 1],
                    expected_root_object_id=pricing_policy_id,
                )
            ],
        )

        price_id = stable_price_id(
            coin_id=coin_id,
            name="default-service-price",
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
            snapshot_key="default-v1",
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="Price",
            root_class_fqn=ECONOMY_PRICE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_PRICE_CLASS_FQN,
                    function_name="build",
                    args=[
                        coin_id,
                        "default-service-price",
                        PriceType.fixed.value,
                    ],
                    expected_root_object_id=price_id,
                ),
                ProofCall(
                    target="instance",
                    object_id=ROOT_OBJECT_ID,
                    class_fqn=ECONOMY_PRICE_CLASS_FQN,
                    function_name="create_price_schedule",
                    args=[
                        pricing_policy_id,
                        "default",
                        "2026-03-25T00:00:00Z",
                        1,
                        None,
                        "10.0",
                        None,
                    ],
                ),
                ProofCall(
                    target="instance",
                    object_id=SourceObjectId(price_schedule_id),
                    class_fqn=ECONOMY_PRICE_SCHEDULE_CLASS_FQN,
                    function_name="capture_rate_snapshot",
                    args=[
                        "default-v1",
                        "10.0",
                        "2026-03-25T00:00:01Z",
                    ],
                ),
            ],
        )

        permit_nonce = 1
        permit_id = stable_smart_contract_permit_id(
            smart_contract_id=smart_contract_id,
            finance_entity_id=payer_finance_entity_id,
            permit_nonce=permit_nonce,
        )
        expires_at = _json_datetime(datetime.now(UTC) + timedelta(hours=2))

        _, contract_setup_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="SmartContract",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="add_member",
                    object_id=SourceObjectId(smart_contract_id),
                    args=[payer_finance_entity_id, SmartContractMemberType.payer.value],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="add_member",
                    object_id=SourceObjectId(smart_contract_id),
                    args=[
                        receiver_finance_entity_id,
                        SmartContractMemberType.receiver.value,
                    ],
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="open_session_permit",
                    object_id=SourceObjectId(smart_contract_id),
                    args=[
                        payer_finance_entity_id,
                        permit_nonce,
                        "50.0",
                        expires_at,
                        price_schedule_id,
                        coin_id,
                        None,
                    ],
                ),
            ],
        )
        contract_setup_assertions.expect_instance(permit_id)
        assert contract_setup_assertions.primitive(instance_id=permit_id, field_name="nonce") == 0
        _expect_uuid_primitive(
            contract_setup_assertions,
            instance_id=permit_id,
            field_name="price_schedule_id",
            expected=price_schedule_id,
        )

        smart_contract_projection_hash = opgs["SmartContract"].projection_hash
        await _assert_failed_no_commit(
            runtime=runtime,
            lane=receiver_lane,
            projection_hash=smart_contract_projection_hash,
            object_id=SourceObjectId(smart_contract_id),
            class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            function_name="reserve_operation",
            args=[
                permit_id,
                2,
                payer_finance_entity_id,
                payer_wallet_public_id,
                1,
                "args:hash:1",
                "10.0",
                rate_snapshot_id,
                _json_datetime(datetime.now(UTC) + timedelta(minutes=30)),
                coin_id,
            ],
            error_fragment="permit_id mismatch",
        )
        await _assert_failed_no_commit(
            runtime=runtime,
            lane=receiver_lane,
            projection_hash=smart_contract_projection_hash,
            object_id=SourceObjectId(smart_contract_id),
            class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            function_name="reserve_operation",
            args=[
                permit_id,
                permit_nonce,
                payer_finance_entity_id,
                payer_wallet_public_id,
                1,
                "args:hash:1",
                "10.0",
                rate_snapshot_id,
                _json_datetime(datetime.now(UTC) + timedelta(minutes=30)),
                uuid4(),
            ],
            error_fragment="reservation coin_id must match permit coin_id",
        )

        reservation_id = stable_smart_contract_reservation_id(
            smart_contract_permit_id=permit_id,
            op_nonce=1,
        )
        settlement_id = stable_smart_contract_settlement_id(
            smart_contract_reservation_id=reservation_id,
        )
        escrow_id = stable_escrow_id(
            wallet_public_id=payer_wallet_public_id,
            op_nonce=1,
        )
        transaction_id = stable_transaction_id(
            capital_origin_id=payer_wallet_public_id,
            target_wallet_public_id=receiver_wallet_public_id,
            coin_id=coin_id,
            nonce=1,
        )
        _, reserve_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="SmartContract",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="reserve_operation",
                    object_id=SourceObjectId(smart_contract_id),
                    args=[
                        permit_id,
                        permit_nonce,
                        payer_finance_entity_id,
                        payer_wallet_public_id,
                        1,
                        "args:hash:1",
                        "10.0",
                        rate_snapshot_id,
                        _json_datetime(datetime.now(UTC) + timedelta(minutes=30)),
                        coin_id,
                    ],
                )
            ],
        )
        reserve_assertions.expect_instance(reservation_id)
        _expect_enum_value(
            reserve_assertions,
            instance_id=reservation_id,
            field_name="status",
            expected="pending",
        )
        assert reserve_assertions.primitive(instance_id=permit_id, field_name="nonce") == 1
        await _assert_failed_no_commit(
            runtime=runtime,
            lane=receiver_lane,
            projection_hash=smart_contract_projection_hash,
            object_id=SourceObjectId(escrow_id),
            class_fqn=ECONOMY_ESCROW_CLASS_FQN,
            function_name="release",
            args=[],
            error_fragment=("requires linked reservation status " "cancelled/executed/expired/settled"),
        )

        await _assert_failed_no_commit(
            runtime=runtime,
            lane=receiver_lane,
            projection_hash=smart_contract_projection_hash,
            object_id=SourceObjectId(smart_contract_id),
            class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            function_name="settle_operation",
            args=[
                permit_id,
                reservation_id,
                "2.0",
                payer_finance_entity_id,
                payer_wallet_public_id,
                uuid4(),
                receiver_wallet_public_id,
                coin_id,
            ],
            error_fragment="not a receiver member",
        )
        await _assert_failed_no_commit(
            runtime=runtime,
            lane=receiver_lane,
            projection_hash=smart_contract_projection_hash,
            object_id=SourceObjectId(smart_contract_id),
            class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            function_name="settle_operation",
            args=[
                permit_id,
                reservation_id,
                "11.0",
                payer_finance_entity_id,
                payer_wallet_public_id,
                receiver_finance_entity_id,
                receiver_wallet_public_id,
                coin_id,
            ],
            error_fragment="exceeds reserved max_cost",
        )

        _, prepare_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="SmartContract",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="prepare_settlement",
                    object_id=SourceObjectId(smart_contract_id),
                    args=[
                        permit_id,
                        reservation_id,
                        "7.0",
                        payer_finance_entity_id,
                        payer_wallet_public_id,
                        receiver_finance_entity_id,
                        receiver_wallet_public_id,
                        coin_id,
                    ],
                )
            ],
        )
        prepare_assertions.expect_instance(settlement_id)
        _expect_enum_value(
            prepare_assertions,
            instance_id=reservation_id,
            field_name="status",
            expected="executed",
        )
        assert prepare_assertions.primitive(instance_id=reservation_id, field_name="final_cost") == "7"
        _expect_enum_value(
            prepare_assertions,
            instance_id=settlement_id,
            field_name="status",
            expected="prepared",
        )
        assert prepare_assertions.primitive(instance_id=settlement_id, field_name="final_cost") == "7"

        release_response = await _invoke_instance(
            runtime=runtime,
            lane=receiver_lane,
            projection_hash=smart_contract_projection_hash,
            object_id=SourceObjectId(escrow_id),
            class_fqn=ECONOMY_ESCROW_CLASS_FQN,
            function_name="release",
        )
        assert release_response.status == "succeeded", release_response.error
        assert release_response.commit_id is not None

        _, finalize_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=receiver_lane,
            opg_name="SmartContract",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="finalize_settlement",
                    object_id=SourceObjectId(smart_contract_id),
                    args=[
                        permit_id,
                        reservation_id,
                        "7.0",
                        payer_finance_entity_id,
                        payer_wallet_public_id,
                        receiver_finance_entity_id,
                        receiver_wallet_public_id,
                        coin_id,
                    ],
                )
            ],
        )
        finalize_assertions.expect_instance(settlement_id)
        _expect_enum_value(
            finalize_assertions,
            instance_id=reservation_id,
            field_name="status",
            expected="settled",
        )
        assert finalize_assertions.primitive(instance_id=reservation_id, field_name="final_cost") == "7"
        _expect_enum_value(
            finalize_assertions,
            instance_id=escrow_id,
            field_name="status",
            expected="completed",
        )
        _expect_enum_value(
            finalize_assertions,
            instance_id=settlement_id,
            field_name="status",
            expected="settled",
        )
        assert finalize_assertions.primitive(instance_id=permit_id, field_name="nonce") == 1

        transaction_projection_hash = opgs["Transaction"].projection_hash
        store = FSCommitStore()
        assert receiver_lane.branch_id is not None
        smart_contract_head = await store.head(
            branch_id=receiver_lane.branch_id,
            projection_hash=smart_contract_projection_hash,
        )
        assert smart_contract_head and smart_contract_head.get(
            "object_instance_graph_id"
        ), "Missing smart_contract head after finalize"
        _transaction_ocgi, transaction_opgi = resolve_meta_graph_ocgi_opgi(
            index=idx,
            projection_hash=transaction_projection_hash,
        )
        assert transaction_opgi is not None, "Missing transaction projection identity"
        transaction_branch_id = stable_portal_branch_id(
            object_instance_graph_id=UUID(str(smart_contract_head["object_instance_graph_id"])),
            object_projection_graph_identity_id=transaction_opgi.id,
            target_object_id=transaction_id,
        )
        transaction_head = await store.head(
            branch_id=transaction_branch_id,
            projection_hash=transaction_projection_hash,
        )
        assert transaction_head and transaction_head.get("commit_id"), "Missing transaction head after finalize"
        transaction_oig, _ = await OIGMaterializer().get(
            branch_id=transaction_branch_id,
            ocg=idx.ocg,
            opg=opgs["Transaction"],
            commit_id=UUID(str(transaction_head["commit_id"])),
            oig_id=UUID(str(transaction_head["object_instance_graph_id"])),
            attribute_configs_by_id=idx.attribute_configs_by_id,
            class_configs_by_id=idx.class_configs_by_id,
        )
        transaction_assertions = MetaOIGAssertions(oig=transaction_oig, index=idx)
        transaction_assertions.expect_instance(transaction_id)
        assert transaction_assertions.primitive(instance_id=transaction_id, field_name="coin_amount") == "7"
        _expect_uuid_primitive(
            transaction_assertions,
            instance_id=transaction_id,
            field_name="source_wallet_public_id",
            expected=payer_wallet_public_id,
        )
        _expect_uuid_primitive(
            transaction_assertions,
            instance_id=transaction_id,
            field_name="target_wallet_public_id",
            expected=receiver_wallet_public_id,
        )
