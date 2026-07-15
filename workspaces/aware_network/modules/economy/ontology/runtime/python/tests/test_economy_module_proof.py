from __future__ import annotations

from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.handlers.impl.wallet import wallet as wallet_impl
from aware_economy.handlers.impl.wallet import wallet_private as wallet_private_impl
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
    run_meta_runtime_proof,
)


ECONOMY_FINANCE_ENTITY_CLASS_FQN = "aware_economy.finance.FinanceEntity"
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


@pytest.mark.asyncio
async def test_wallet_build_paths_reject_dev_private_key_material() -> None:
    with pytest.raises(ValueError, match="not dev material"):
        await wallet_impl.build(
            address="0x1111111111111111111111111111111111111111",
            public_key="public-key",
            private_key_encrypted="dev:private-key",
        )
    with pytest.raises(ValueError, match="not dev material"):
        await wallet_private_impl.build(private_key_encrypted="dev:private-key")


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


def _expect_uuid_primitive(
    assertions: MetaOIGAssertions,
    *,
    instance_id: UUID,
    field_name: str,
    expected: UUID,
) -> None:
    value = assertions.primitive(instance_id=instance_id, field_name=field_name)
    assert value in {expected, str(expected)}


@pytest.mark.asyncio
async def test_economy_finance_entity_build_module_proof(tmp_path: Path) -> None:
    repo_root = REPO_ROOT

    import aware_economy_ontology  # noqa: F401
    from aware_economy_ontology.finance.finance_entity import FinanceEntity
    from aware_economy_ontology.stable_ids import (
        stable_finance_entity_id,
        stable_wallet_id,
        stable_wallet_private_id,
        stable_wallet_public_id,
    )
    from aware_economy_ontology.wallet.wallet import Wallet

    identity_id = uuid4()
    custody = derive_wallet_custody_material(
        identity_id=identity_id,
        role_key="primary",
    )
    expected_public_key = custody.public_key
    expected_address = custody.address
    expected_private_key_encrypted = custody.private_key_encrypted

    expected_wallet_public_id = stable_wallet_public_id(
        public_key=expected_public_key,
    )
    expected_wallet_private_id = stable_wallet_private_id(
        private_key_encrypted=expected_private_key_encrypted,
    )
    expected_wallet_id = stable_wallet_id(
        public_key=expected_public_key,
        private_key_encrypted=expected_private_key_encrypted,
    )
    expected_finance_entity_id = stable_finance_entity_id(identity_id=identity_id)

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

        wallet_result, wallet_assertions = await run_meta_runtime_proof(
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
                        expected_address,
                        expected_public_key,
                        expected_private_key_encrypted,
                    ],
                    expected_root_object_id=expected_wallet_id,
                )
            ],
        )

        assert wallet_result.root_object_id == expected_wallet_id
        wallet_assertions.expect_root(expected_wallet_id)
        wallet_assertions.expect_instance(expected_wallet_id)
        wallet_assertions.expect_instance(expected_wallet_public_id)
        wallet_assertions.expect_instance(expected_wallet_private_id)
        wallet_assertions.expect_edge(
            source_id=expected_wallet_id,
            target_id=expected_wallet_public_id,
            relationship_name="wallet_public",
        )
        wallet_assertions.expect_edge(
            source_id=expected_wallet_id,
            target_id=expected_wallet_private_id,
            relationship_name="wallet_private",
        )
        wallet_assertions.expect_primitive(
            instance_id=expected_wallet_id,
            field_name="public_key",
            expected=expected_public_key,
        )
        wallet_assertions.expect_primitive(
            instance_id=expected_wallet_id,
            field_name="private_key_encrypted",
            expected=expected_private_key_encrypted,
        )
        wallet_assertions.expect_primitive(
            instance_id=expected_wallet_public_id,
            field_name="address",
            expected=expected_address,
        )
        wallet_assertions.expect_primitive(
            instance_id=expected_wallet_public_id,
            field_name="public_key",
            expected=expected_public_key,
        )
        wallet_assertions.expect_primitive(
            instance_id=expected_wallet_public_id,
            field_name="nonce_counter",
            expected=0,
        )
        wallet_assertions.expect_primitive(
            instance_id=expected_wallet_private_id,
            field_name="private_key_encrypted",
            expected=expected_private_key_encrypted,
        )

        wallet_payload = wallet_result.responses[-1].payload
        assert isinstance(wallet_payload, dict)
        wallet_created_payload = wallet_payload.get("value", wallet_payload)
        wallet_created = Wallet.model_validate(wallet_created_payload)
        assert wallet_created.id == expected_wallet_id
        assert wallet_created.public_key == expected_public_key
        assert wallet_created.private_key_encrypted == expected_private_key_encrypted
        assert wallet_created.wallet_public_id == expected_wallet_public_id
        assert wallet_created.wallet_private_id == expected_wallet_private_id

        finance_result, finance_assertions = await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="FinanceEntity",
            root_class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_FINANCE_ENTITY_CLASS_FQN,
                    function_name="build",
                    args=[identity_id, expected_wallet_id, "primary"],
                    expected_root_object_id=expected_finance_entity_id,
                )
            ],
        )

        assert finance_result.root_object_id == expected_finance_entity_id
        finance_assertions.expect_root(expected_finance_entity_id)
        finance_assertions.expect_instance(expected_finance_entity_id)
        _expect_uuid_primitive(
            finance_assertions,
            instance_id=expected_finance_entity_id,
            field_name="identity_id",
            expected=identity_id,
        )
        _expect_uuid_primitive(
            finance_assertions,
            instance_id=expected_finance_entity_id,
            field_name="wallet_id",
            expected=expected_wallet_id,
        )
        finance_assertions.expect_primitive(
            instance_id=expected_finance_entity_id,
            field_name="role_key",
            expected="primary",
        )

        finance_payload = finance_result.responses[-1].payload
        assert isinstance(finance_payload, dict)
        finance_created_payload = finance_payload.get("value", finance_payload)
        finance_created = FinanceEntity.model_validate(finance_created_payload)
        assert finance_created.id == expected_finance_entity_id
        assert finance_created.identity_id == identity_id
        assert finance_created.wallet_id == expected_wallet_id
        assert finance_created.role_key == "primary"
