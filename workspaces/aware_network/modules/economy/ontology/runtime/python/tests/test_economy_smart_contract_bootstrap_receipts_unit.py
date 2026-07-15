from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.wallet_custody import derive_wallet_custody_material
from aware_meta.runtime import (
    MetaGraphGeneratedConstructorBootstrapModule,
    MetaGraphGeneratedLanguageHandlerModule,
    MetaGraphRuntime,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.testing import (
    IsolatedMetaAwareRoot as IsolatedAwareRoot,
    LaneIds,
    MetaOIGAssertions,
    ProofCall,
    ROOT_OBJECT_ID,
    run_meta_runtime_proof,
)


ECONOMY_FINANCE_ENTITY_CLASS_FQN = "aware_economy.finance.FinanceEntity"
ECONOMY_SMART_CONTRACT_CLASS_FQN = "aware_economy.smart_contract.SmartContract"
ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN = (
    "aware_economy.smart_contract.SmartContractConfig"
)
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


@pytest.mark.asyncio
async def test_economy_smart_contract_bootstrap_receipts_are_deterministic(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT

    import aware_economy_ontology  # noqa: F401
    from aware_economy_ontology.smart_contract.smart_contract_enums import (
        SmartContractMemberType,
        SmartContractType,
    )
    from aware_economy_ontology.stable_ids import (
        stable_finance_entity_id,
        stable_smart_contract_config_id,
        stable_smart_contract_id,
        stable_smart_contract_member_id,
        stable_wallet_id,
        stable_wallet_private_id,
        stable_wallet_public_id,
    )

    with IsolatedAwareRoot(
        tmp_path / "aware_root", persistence_backend="fs"
    ) as aware_root:
        runtime = _build_economy_meta_runtime(
            repo_root=repo_root,
            aware_root=aware_root,
        )
        lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )

        provider_identity_id = uuid4()
        wallet_address, wallet_public_key, wallet_private_key_encrypted = (
            _custody_wallet_inputs(identity_id=provider_identity_id)
        )
        provider_wallet_public_id = stable_wallet_public_id(
            public_key=wallet_public_key,
        )
        provider_wallet_private_id = stable_wallet_private_id(
            private_key_encrypted=wallet_private_key_encrypted,
        )
        provider_wallet_id = stable_wallet_id(
            public_key=wallet_public_key,
            private_key_encrypted=wallet_private_key_encrypted,
        )
        provider_finance_entity_id = stable_finance_entity_id(
            identity_id=provider_identity_id,
        )

        _, wallet_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Wallet",
            root_class_fqn=ECONOMY_WALLET_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_WALLET_CLASS_FQN,
                    function_name="build",
                    args=[
                        wallet_address,
                        wallet_public_key,
                        wallet_private_key_encrypted,
                    ],
                    expected_root_object_id=provider_wallet_id,
                )
            ],
        )
        wallet_assertions.expect_instance(provider_wallet_public_id)
        wallet_assertions.expect_instance(provider_wallet_private_id)

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="FinanceEntity",
            root_class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
                    function_name="build",
                    args=[provider_identity_id, provider_wallet_id],
                    expected_root_object_id=provider_finance_entity_id,
                )
            ],
        )

        smart_contract_config_name = "AwareInferenceContract"
        smart_contract_config_id = stable_smart_contract_config_id(
            name=smart_contract_config_name,
            type=SmartContractType.utility.value,
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="SmartContractConfig",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_SMART_CONTRACT_CONFIG_CLASS_FQN,
                    function_name="build",
                    args=[
                        smart_contract_config_name,
                        "Inference smart-contract template",
                        SmartContractType.utility.value,
                    ],
                    expected_root_object_id=smart_contract_config_id,
                )
            ],
        )

        blockchain_address = "dev:bootstrap"
        smart_contract_id = stable_smart_contract_id(
            smart_contract_config_id=smart_contract_config_id,
            blockchain_address=blockchain_address,
        )
        member_id = stable_smart_contract_member_id(
            smart_contract_id=smart_contract_id,
            finance_entity_id=provider_finance_entity_id,
            type=SmartContractMemberType.receiver.value,
        )
        _, assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="SmartContract",
            root_class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="build_via_smart_contract_config",
                    args=[smart_contract_config_id, blockchain_address],
                    expected_root_object_id=smart_contract_id,
                ),
                ProofCall(
                    target="instance",
                    class_fqn=ECONOMY_SMART_CONTRACT_CLASS_FQN,
                    function_name="add_member",
                    object_id=ROOT_OBJECT_ID,
                    args=[
                        provider_finance_entity_id,
                        SmartContractMemberType.receiver.value,
                    ],
                ),
            ],
        )

        assertions.expect_instance(member_id)
        _expect_uuid_primitive(
            assertions,
            instance_id=member_id,
            field_name="smart_contract_id",
            expected=smart_contract_id,
        )
        _expect_uuid_primitive(
            assertions,
            instance_id=member_id,
            field_name="finance_entity_id",
            expected=provider_finance_entity_id,
        )
        _expect_enum_value(
            assertions,
            instance_id=member_id,
            field_name="type",
            expected=SmartContractMemberType.receiver.value,
        )
