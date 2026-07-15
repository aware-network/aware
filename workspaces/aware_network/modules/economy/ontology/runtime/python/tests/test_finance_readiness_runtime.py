from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT, economy_package_manifest_paths
from aware_economy.finance_readiness import (
    EconomyFinanceReadinessOperationContext,
    ensure_finance_entity,
    resolve_economy_finance_readiness_runtime_context,
    resolve_finance_entity_readiness,
)
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_economy.wallet_custody import (
    WALLET_CUSTODY_PREFIX,
    derive_wallet_custody_material,
)
from aware_economy_ontology.stable_ids import (
    stable_finance_entity_id,
    stable_wallet_id,
    stable_wallet_public_id,
)
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


@pytest.mark.asyncio
async def test_ensure_finance_entity_commits_role_wallet_readiness(tmp_path) -> None:
    actor_id = uuid4()
    custody = derive_wallet_custody_material(
        identity_id=actor_id,
        role_key="PRIMARY",
    )
    expected_finance_entity_id = stable_finance_entity_id(identity_id=actor_id)
    expected_wallet_id = stable_wallet_id(
        public_key=custody.public_key,
        private_key_encrypted=custody.private_key_encrypted,
    )
    expected_wallet_public_id = stable_wallet_public_id(
        public_key=custody.public_key,
    )

    assert custody.role_key == "primary"
    assert custody.private_key_encrypted.startswith(f"{WALLET_CUSTODY_PREFIX}:")
    assert not custody.private_key_encrypted.startswith("dev:")

    with IsolatedAwareRoot(
        tmp_path / "aware_root",
        persistence_backend="fs",
    ) as aware_root:
        runtime = _build_economy_meta_runtime(aware_root=aware_root)
        assert runtime.context is not None
        runtime_context = resolve_economy_finance_readiness_runtime_context(
            lane_binder=runtime,
            index=runtime.context.index,
        )

        missing = await resolve_finance_entity_readiness(
            runtime_context=runtime_context,
            actor_id=actor_id,
            finance_role_key="PRIMARY",
        )

        assert missing.finance_role_key == "primary"
        assert missing.finance_entity_id == expected_finance_entity_id
        assert missing.wallet_id == expected_wallet_id
        assert missing.wallet_public_id == expected_wallet_public_id
        assert missing.finance_entity_ready is False
        assert missing.wallet_ready is False
        assert missing.idempotent_replay is False

        created = await ensure_finance_entity(
            runtime_context=runtime_context,
            operation_context=EconomyFinanceReadinessOperationContext(
                actor_id=actor_id,
            ),
            actor_id=actor_id,
            finance_role_key="PRIMARY",
            commit=True,
            publish=False,
        )

        assert created.finance_role_key == "primary"
        assert created.finance_entity_id == expected_finance_entity_id
        assert created.wallet_id == expected_wallet_id
        assert created.wallet_public_id == expected_wallet_public_id
        assert created.finance_entity_ready is True
        assert created.wallet_ready is True
        assert created.idempotent_replay is False

        hydrated = await resolve_finance_entity_readiness(
            runtime_context=runtime_context,
            actor_id=actor_id,
            finance_role_key="primary",
        )

        assert hydrated.finance_entity_ready is True
        assert hydrated.wallet_ready is True
        assert hydrated.idempotent_replay is True

        replay = await ensure_finance_entity(
            runtime_context=runtime_context,
            operation_context=EconomyFinanceReadinessOperationContext(
                actor_id=actor_id,
            ),
            actor_id=actor_id,
            finance_role_key="primary",
            commit=True,
            publish=False,
        )

        assert replay.finance_entity_id == expected_finance_entity_id
        assert replay.wallet_id == expected_wallet_id
        assert replay.wallet_public_id == expected_wallet_public_id
        assert replay.idempotent_replay is True
