from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_code.types import JsonArray, JsonObject, JsonValue
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.wallet_custody import derive_wallet_custody_material
from aware_experience.program.language import (
    compile_invocation_plans,
    encode_invocation_plan_artifact,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
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
    SourceObjectId,
    run_meta_runtime_proof,
)
from aware_meta_ontology.function.function_config import FunctionConfig
from aware_meta_ontology.graph.instance.object_instance_graph import (
    ObjectInstanceGraph,
)


ECONOMY_COIN_CLASS_FQN = "aware_economy.coin.Coin"
ECONOMY_TRANSACTION_CLASS_FQN = "aware_economy.transaction.Transaction"
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


def _load_invocation_plan_artifact(
    *,
    repo_root: Path,
    program_rel_path: str,
    program_name: str,
) -> dict[str, object]:
    program_source = (repo_root / program_rel_path).read_text(encoding="utf-8")
    plans = compile_invocation_plans(program_source)
    matches = [plan for plan in plans if plan.name == program_name]
    if len(matches) != 1:
        raise AssertionError(f"Expected one InvocationPlan for {program_name!r}, got {len(matches)}")
    return encode_invocation_plan_artifact(matches[0])


def _artifact_plan_name(artifact: dict[str, object]) -> str:
    plan = artifact.get("plan")
    if not isinstance(plan, dict):
        raise AssertionError(f"Invocation plan artifact missing plan: {artifact!r}")
    name = plan.get("name")
    if not isinstance(name, str):
        raise AssertionError(f"Invocation plan artifact missing plan.name: {artifact!r}")
    return name


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


async def _require_head_ids(
    *,
    branch_id: UUID,
    projection_hash: str,
    label: str,
) -> tuple[UUID, UUID]:
    head = await FSCommitStore().head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    if not head or not head.get("commit_id") or not head.get("object_instance_graph_id"):
        raise AssertionError(f"Missing {label} head")
    return (
        UUID(str(head["commit_id"])),
        UUID(str(head["object_instance_graph_id"])),
    )


async def _assert_head_commit(
    *,
    branch_id: UUID,
    projection_hash: str,
    expected_commit_id: UUID,
    label: str,
) -> None:
    commit_id, _ = await _require_head_ids(
        branch_id=branch_id,
        projection_hash=projection_hash,
        label=label,
    )
    assert commit_id == expected_commit_id


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
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, tuple):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, list):
        return [_jsonify_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonify_value(item) for key, item in value.items()}
    return cast(JsonValue, value)


async def _apply_create_wallet_transfer_sequence(
    *,
    runtime: MetaGraphRuntime,
    transaction_lane: LaneIds,
    source_wallet_lane: LaneIds,
    target_wallet_lane: LaneIds,
    wallet_projection_hash: str,
    transaction_id: UUID,
    source_wallet_id: UUID,
    source_wallet_public_id: UUID,
    source_expected_coin_balance: Decimal,
    source_new_coin_balance: Decimal,
    target_wallet_id: UUID,
    target_wallet_public_id: UUID,
    target_expected_coin_balance: Decimal,
    target_new_coin_balance: Decimal,
    coin_id: UUID,
    coin_amount: Decimal,
    nonce: int,
    description: str,
) -> None:
    await run_meta_runtime_proof(
        runtime=runtime,
        lane=transaction_lane,
        opg_name="Transaction",
        root_class_fqn=ECONOMY_TRANSACTION_CLASS_FQN,
        calls=[
            ProofCall(
                target="constructor",
                class_fqn=ECONOMY_TRANSACTION_CLASS_FQN,
                function_name="create",
                args=[
                    source_wallet_public_id,
                    source_wallet_public_id,
                    target_wallet_public_id,
                    coin_id,
                    format(coin_amount, "f"),
                    nonce,
                    description,
                    None,
                ],
                expected_root_object_id=transaction_id,
                allow_noop_commit=True,
            )
        ],
    )
    calls = (
        await _invoke_instance(
            runtime=runtime,
            lane=source_wallet_lane,
            projection_hash=wallet_projection_hash,
            object_id=SourceObjectId(source_wallet_id),
            class_fqn=ECONOMY_WALLET_CLASS_FQN,
            function_name="reconcile_coin_balance",
            args=[
                coin_id,
                format(source_expected_coin_balance, "f"),
                format(source_new_coin_balance, "f"),
            ],
        ),
        await _invoke_instance(
            runtime=runtime,
            lane=target_wallet_lane,
            projection_hash=wallet_projection_hash,
            object_id=SourceObjectId(target_wallet_id),
            class_fqn=ECONOMY_WALLET_CLASS_FQN,
            function_name="reconcile_coin_balance",
            args=[
                coin_id,
                format(target_expected_coin_balance, "f"),
                format(target_new_coin_balance, "f"),
            ],
        ),
    )
    for response in calls:
        assert response.status == "succeeded", response.error or "\n".join(response.logs)


@pytest.mark.asyncio
async def test_meta_program_sequence_create_wallet_transfer_idempotent(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_economy_ontology  # noqa: F401
    from aware_economy_ontology.coin.coin_enums import CoinType
    from aware_economy_ontology.stable_ids import (
        stable_coin_id,
        stable_transaction_id,
        stable_wallet_balance_id,
        stable_wallet_id,
        stable_wallet_private_id,
        stable_wallet_public_id,
    )

    create_wallet_transfer_invocation_plan_artifact = _load_invocation_plan_artifact(
        repo_root=repo_root,
        program_rel_path=(
            "workspaces/aware_network/modules/economy/experiences/"
            "aware_economy/programs/transaction/"
            "create_wallet_transfer_v1.aware"
        ),
        program_name="CreateWalletTransfer_v1",
    )
    reconcile_transfer_wallet_balances_invocation_plan_artifact = _load_invocation_plan_artifact(
        repo_root=repo_root,
        program_rel_path=(
            "workspaces/aware_network/modules/economy/experiences/"
            "aware_economy/programs/finance/"
            "reconcile_transfer_wallet_balances_v1.aware"
        ),
        program_name="ReconcileTransferWalletBalances_v1",
    )
    assert _artifact_plan_name(create_wallet_transfer_invocation_plan_artifact) == "CreateWalletTransfer_v1"
    assert (
        _artifact_plan_name(reconcile_transfer_wallet_balances_invocation_plan_artifact)
        == "ReconcileTransferWalletBalances_v1"
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
            "Coin",
            "Transaction",
        }
        assert required.issubset(opgs.keys())

        actor_id = uuid4()
        source_wallet_lane = LaneIds(
            branch_id=uuid4(),
            actor_id=actor_id,
        )
        target_wallet_lane = LaneIds(
            branch_id=uuid4(),
            actor_id=actor_id,
        )
        coin_lane = LaneIds(
            branch_id=uuid4(),
            actor_id=actor_id,
        )
        transaction_lane = LaneIds(
            branch_id=uuid4(),
            actor_id=actor_id,
        )
        assert source_wallet_lane.branch_id is not None
        assert target_wallet_lane.branch_id is not None
        assert transaction_lane.branch_id is not None

        source_identity_id = uuid4()
        target_identity_id = uuid4()
        source_address, source_public_key, source_private_key_encrypted = _custody_wallet_inputs(
            identity_id=source_identity_id
        )
        target_address, target_public_key, target_private_key_encrypted = _custody_wallet_inputs(
            identity_id=target_identity_id
        )

        source_wallet_public_id = stable_wallet_public_id(public_key=source_public_key)
        _ = stable_wallet_private_id(private_key_encrypted=source_private_key_encrypted)
        source_wallet_id = stable_wallet_id(
            public_key=source_public_key,
            private_key_encrypted=source_private_key_encrypted,
        )

        target_wallet_public_id = stable_wallet_public_id(public_key=target_public_key)
        _ = stable_wallet_private_id(private_key_encrypted=target_private_key_encrypted)
        target_wallet_id = stable_wallet_id(
            public_key=target_public_key,
            private_key_encrypted=target_private_key_encrypted,
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=source_wallet_lane,
            opg_name="Wallet",
            root_class_fqn=ECONOMY_WALLET_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        source_address,
                        source_public_key,
                        source_private_key_encrypted,
                    ],
                    expected_root_object_id=source_wallet_id,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=target_wallet_lane,
            opg_name="Wallet",
            root_class_fqn=ECONOMY_WALLET_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        target_address,
                        target_public_key,
                        target_private_key_encrypted,
                    ],
                    expected_root_object_id=target_wallet_id,
                )
            ],
        )

        coin_id = stable_coin_id(symbol="USD")
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=coin_lane,
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

        wallet_projection_hash = opgs["Wallet"].projection_hash
        source_start_balance = Decimal("12.0")
        target_start_balance = Decimal("1.5")
        transfer_amount = Decimal("4.0")

        for lane, wallet_id, balance in (
            (source_wallet_lane, source_wallet_id, source_start_balance),
            (target_wallet_lane, target_wallet_id, target_start_balance),
        ):
            response = await _invoke_instance(
                runtime=runtime,
                lane=lane,
                projection_hash=wallet_projection_hash,
                object_id=SourceObjectId(wallet_id),
                class_fqn=ECONOMY_WALLET_CLASS_FQN,
                function_name="set_coin_balance",
                args=[coin_id, format(balance, "f")],
            )
            assert response.status == "succeeded", response.error

        nonce = 7
        transaction_id = stable_transaction_id(
            capital_origin_id=source_wallet_public_id,
            target_wallet_public_id=target_wallet_public_id,
            coin_id=coin_id,
            nonce=nonce,
        )
        transaction_projection_hash = opgs["Transaction"].projection_hash

        await _apply_create_wallet_transfer_sequence(
            runtime=runtime,
            transaction_lane=transaction_lane,
            source_wallet_lane=source_wallet_lane,
            target_wallet_lane=target_wallet_lane,
            wallet_projection_hash=wallet_projection_hash,
            transaction_id=transaction_id,
            source_wallet_id=source_wallet_id,
            source_wallet_public_id=source_wallet_public_id,
            source_expected_coin_balance=source_start_balance,
            source_new_coin_balance=source_start_balance - transfer_amount,
            target_wallet_id=target_wallet_id,
            target_wallet_public_id=target_wallet_public_id,
            target_expected_coin_balance=target_start_balance,
            target_new_coin_balance=target_start_balance + transfer_amount,
            coin_id=coin_id,
            coin_amount=transfer_amount,
            nonce=nonce,
            description="wallet-transfer-proof",
        )

        source_wallet_commit_after_first, _ = await _require_head_ids(
            branch_id=source_wallet_lane.branch_id,
            projection_hash=wallet_projection_hash,
            label="source wallet after first transfer sequence",
        )
        source_wallet_oig = await _materialize_lane_head(
            index=idx,
            branch_id=source_wallet_lane.branch_id,
            projection_hash=wallet_projection_hash,
        )
        source_wallet_assertions = MetaOIGAssertions(
            oig=source_wallet_oig,
            index=idx,
        )
        source_wallet_balance_id = stable_wallet_balance_id(
            wallet_id=source_wallet_id,
            coin_id=coin_id,
        )
        assert (
            source_wallet_assertions.primitive(
                instance_id=source_wallet_balance_id,
                field_name="balance",
            )
            == "8"
        )

        target_wallet_commit_after_first, _ = await _require_head_ids(
            branch_id=target_wallet_lane.branch_id,
            projection_hash=wallet_projection_hash,
            label="target wallet after first transfer sequence",
        )
        target_wallet_oig = await _materialize_lane_head(
            index=idx,
            branch_id=target_wallet_lane.branch_id,
            projection_hash=wallet_projection_hash,
        )
        target_wallet_assertions = MetaOIGAssertions(
            oig=target_wallet_oig,
            index=idx,
        )
        target_wallet_balance_id = stable_wallet_balance_id(
            wallet_id=target_wallet_id,
            coin_id=coin_id,
        )
        assert (
            target_wallet_assertions.primitive(
                instance_id=target_wallet_balance_id,
                field_name="balance",
            )
            == "5.5"
        )

        transaction_commit_after_first, _ = await _require_head_ids(
            branch_id=transaction_lane.branch_id,
            projection_hash=transaction_projection_hash,
            label="transaction after first transfer sequence",
        )
        transaction_oig = await _materialize_lane_head(
            index=idx,
            branch_id=transaction_lane.branch_id,
            projection_hash=transaction_projection_hash,
        )
        transaction_assertions = MetaOIGAssertions(oig=transaction_oig, index=idx)
        transaction_assertions.expect_instance(transaction_id)
        assert (
            transaction_assertions.primitive(
                instance_id=transaction_id,
                field_name="coin_amount",
            )
            == "4"
        )
        _expect_uuid_primitive(
            transaction_assertions,
            instance_id=transaction_id,
            field_name="source_wallet_public_id",
            expected=source_wallet_public_id,
        )
        _expect_uuid_primitive(
            transaction_assertions,
            instance_id=transaction_id,
            field_name="target_wallet_public_id",
            expected=target_wallet_public_id,
        )
        _expect_enum_value(
            transaction_assertions,
            instance_id=transaction_id,
            field_name="status",
            expected="created",
        )

        await _apply_create_wallet_transfer_sequence(
            runtime=runtime,
            transaction_lane=transaction_lane,
            source_wallet_lane=source_wallet_lane,
            target_wallet_lane=target_wallet_lane,
            wallet_projection_hash=wallet_projection_hash,
            transaction_id=transaction_id,
            source_wallet_id=source_wallet_id,
            source_wallet_public_id=source_wallet_public_id,
            source_expected_coin_balance=source_start_balance,
            source_new_coin_balance=source_start_balance - transfer_amount,
            target_wallet_id=target_wallet_id,
            target_wallet_public_id=target_wallet_public_id,
            target_expected_coin_balance=target_start_balance,
            target_new_coin_balance=target_start_balance + transfer_amount,
            coin_id=coin_id,
            coin_amount=transfer_amount,
            nonce=nonce,
            description="wallet-transfer-proof",
        )

        await _assert_head_commit(
            branch_id=source_wallet_lane.branch_id,
            projection_hash=wallet_projection_hash,
            expected_commit_id=source_wallet_commit_after_first,
            label="source wallet after idempotent transfer rerun",
        )
        await _assert_head_commit(
            branch_id=target_wallet_lane.branch_id,
            projection_hash=wallet_projection_hash,
            expected_commit_id=target_wallet_commit_after_first,
            label="target wallet after idempotent transfer rerun",
        )
        await _assert_head_commit(
            branch_id=transaction_lane.branch_id,
            projection_hash=transaction_projection_hash,
            expected_commit_id=transaction_commit_after_first,
            label="transaction after idempotent transfer rerun",
        )
