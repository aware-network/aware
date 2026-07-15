from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

from aware_api_runtime.handlers._generated import meta_handlers as api_meta_handlers
from aware_economy.handlers._generated import meta_handlers as economy_meta_handlers
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import MaterializationLaneContext
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
    run_meta_runtime_proof,
)
from aware_service_ontology.service.service_enums import (
    ServiceOperationSettlementPolicy,
)
from aware_service_runtime.handlers._generated import (
    meta_handlers as service_meta_handlers,
)
from aware_service_ontology.stable_ids import (
    stable_service_config_api_id,
    stable_service_config_id,
    stable_service_id,
    stable_service_operation_config_api_endpoint_id,
    stable_service_operation_config_id,
)
from aware_service_runtime.materialization.service import (
    _resolve_canonical_service_config_projection_hash,
    _resolve_canonical_service_projection_hash,
)
from aware_service_runtime.ontology.materialization import (
    materialize_service,
    materialize_service_config,
    materialize_service_config_api,
    materialize_service_operation_config,
    materialize_service_operation_config_api_endpoint,
)
from _service_runtime_test_paths import REPO_ROOT

ECONOMY_COIN_CLASS_FQN = "aware_economy.coin.Coin"
ECONOMY_PRICE_CLASS_FQN = "aware_economy.price.Price"

_API_META_HANDLERS_ANY: Any = api_meta_handlers
_API_META_HANDLER_MODULE = cast(
    MetaGraphGeneratedLanguageHandlerModule,
    _API_META_HANDLERS_ANY,
)
_API_META_BOOTSTRAP_MODULE = cast(
    MetaGraphGeneratedConstructorBootstrapModule,
    _API_META_HANDLERS_ANY,
)
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


def _service_definition_package_manifest_paths(repo_root: Path) -> tuple[Path, ...]:
    return (
        repo_root
        / "workspaces/aware_kernel/modules/storage/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/content/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/code/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/history/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/meta/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/ontology/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_kernel/modules/reactivity/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/attention/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/economy/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/identity/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/api/ontology/structure/aware.toml",
        repo_root / "workspaces/aware_kernel/modules/sdk/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/environment/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/experience/ontology/structure/aware.toml",
        repo_root
        / "workspaces/aware_network/modules/service/ontology/structure/aware.toml",
    )


def _build_service_definition_meta_runtime(
    repo_root: Path,
    *,
    aware_root: Path,
) -> MetaGraphRuntime:
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=_service_definition_package_manifest_paths(repo_root),
        workspace_root=repo_root,
        aware_root=aware_root,
        handler_modules=(
            _API_META_HANDLER_MODULE,
            _ECONOMY_META_HANDLER_MODULE,
            _SERVICE_META_HANDLER_MODULE,
        ),
        bootstrap_modules=(
            _API_META_BOOTSTRAP_MODULE,
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


def _seed_boot_environment(
    *,
    environment_id: UUID,
) -> tuple[UUID, UUID, UUID]:
    from aware_history.stable_ids import stable_branch_id

    process_id = uuid4()
    thread_id = uuid4()
    boot_branch_id = stable_branch_id(
        environment_id=environment_id,
        thread_id=thread_id,
    )
    return process_id, thread_id, boot_branch_id


def test_service_materialization_service_has_no_direct_deprecated_runtime_imports() -> (
    None
):
    source_path = (
        REPO_ROOT
        / "workspaces"
        / "aware_network"
        / "modules"
        / "service"
        / "ontology"
        / "runtime"
        / "python"
        / "aware_service_runtime"
        / "materialization"
        / "service.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".", 1)[0] == "aware_runtime":
                    offenders.append(f"{node.lineno}: import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".", 1)[0] == "aware_runtime":
                offenders.append(f"{node.lineno}: from {node.module} import ...")

    assert offenders == []


@pytest.mark.asyncio
async def test_materialize_service_definition_stack_across_committed_lanes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = REPO_ROOT
    _ = monkeypatch

    import aware_economy_ontology  # noqa: F401
    import aware_service_ontology  # noqa: F401
    from aware_economy_ontology.coin.coin_enums import CoinType
    from aware_economy_ontology.price.price_enums import PriceType
    from aware_economy_ontology.stable_ids import stable_coin_id, stable_price_id

    service_config_name = "compiler"
    service_name = "workspace_compiler"
    operation_config_name = "compile_module"
    api_id = uuid4()
    api_capability_endpoint_id = uuid4()
    coin_id = stable_coin_id(symbol="USD")
    price_name = "aware_compiler_service.compile_module"
    expected_price_id = stable_price_id(
        coin_id=coin_id,
        name=price_name,
        type=PriceType.fixed.value,
    )

    expected_service_config_id = stable_service_config_id(name=service_config_name)
    expected_service_config_api_id = stable_service_config_api_id(
        service_config_id=expected_service_config_id,
        api_id=api_id,
    )
    expected_service_operation_config_id = stable_service_operation_config_id(
        service_config_id=expected_service_config_id,
        name=operation_config_name,
    )
    expected_service_operation_config_api_endpoint_id = (
        stable_service_operation_config_api_endpoint_id(
            service_operation_config_id=expected_service_operation_config_id,
            service_config_api_id=expected_service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
        )
    )
    expected_service_id = stable_service_id(
        service_config_id=expected_service_config_id,
        name=service_name,
    )

    with IsolatedMetaAwareRoot(tmp_path / "aware_root", persistence_backend="fs"):
        runtime = _build_service_definition_meta_runtime(
            repo_root,
            aware_root=tmp_path / "aware_root",
        )
        runtime_index = _runtime_index(runtime)
        environment_id = uuid4()
        boot_process_id, boot_thread_id, _boot_branch_id = _seed_boot_environment(
            environment_id=environment_id
        )
        _ = boot_process_id, boot_thread_id
        lane = LaneIds(
            branch_id=uuid4(),
            actor_id=uuid4(),
        )

        service_config_projection_hash = (
            _resolve_canonical_service_config_projection_hash(runtime_index)
        )
        service_projection_hash = _resolve_canonical_service_projection_hash(
            runtime_index
        )
        active_branch_id = lane.branch_id
        assert active_branch_id is not None

        service_config_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_lane = MaterializationLaneContext(
            branch_id=active_branch_id,
            projection_hash=service_projection_hash,
        )

        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Coin",
            root_class_fqn=ECONOMY_COIN_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_COIN_CLASS_FQN,
                    function_name="build",
                    args=["USD", "US Dollar", CoinType.fiat.value],
                    expected_root_object_id=coin_id,
                )
            ],
        )
        await run_meta_runtime_proof(
            runtime=runtime,
            lane=lane,
            opg_name="Price",
            root_class_fqn=ECONOMY_PRICE_CLASS_FQN,
            calls=[
                ProofCall(
                    target="constructor",
                    class_fqn=ECONOMY_PRICE_CLASS_FQN,
                    function_name="build",
                    args=[coin_id, price_name, PriceType.fixed.value],
                    expected_root_object_id=expected_price_id,
                )
            ],
        )

        materialized_service_config = await materialize_service_config(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            name=service_config_name,
            description="Compiler service catalog",
        )
        materialized_service_config_api = await materialize_service_config_api(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_config_lane,
            service_config_id=expected_service_config_id,
            api_id=api_id,
            description="Shared API bridge",
        )
        materialized_service_operation_config = (
            await materialize_service_operation_config(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_config_id=expected_service_config_id,
                name=operation_config_name,
                description="Compile one module",
                price_id=expected_price_id,
                settlement_policy=ServiceOperationSettlementPolicy.reserve_and_finalize,
            )
        )
        materialized_service_operation_config_api_endpoint = (
            await materialize_service_operation_config_api_endpoint(
                runtime=runtime,
                index=runtime_index,
                actor_id=lane.actor_id,
                target_lane=service_config_lane,
                service_operation_config_id=expected_service_operation_config_id,
                service_config_api_id=expected_service_config_api_id,
                api_capability_endpoint_id=api_capability_endpoint_id,
                description="Public endpoint binding",
            )
        )
        materialized_service = await materialize_service(
            runtime=runtime,
            index=runtime_index,
            actor_id=lane.actor_id,
            target_lane=service_lane,
            service_config_id=expected_service_config_id,
            name=service_name,
            description="Primary compiler service instance",
        )
        assert (
            materialized_service_config.binding.service_config_id
            == expected_service_config_id
        )
        assert (
            materialized_service_config_api.binding.service_config_api_id
            == expected_service_config_api_id
        )
        assert (
            materialized_service_operation_config.binding.service_operation_config_id
            == expected_service_operation_config_id
        )
        assert (
            materialized_service_operation_config_api_endpoint.binding.service_operation_config_api_endpoint_id
            == expected_service_operation_config_api_endpoint_id
        )
        assert materialized_service.binding.service_id == expected_service_id

        assert (
            materialized_service_config.service_config.id == expected_service_config_id
        )
        assert (
            materialized_service_config_api.service_config_api.id
            == expected_service_config_api_id
        )
        assert (
            materialized_service_operation_config.service_operation_config.id
            == expected_service_operation_config_id
        )
        assert (
            materialized_service_operation_config.service_operation_config.price_id
            == expected_price_id
        )
        assert (
            materialized_service_operation_config.service_operation_config.settlement_policy
            == ServiceOperationSettlementPolicy.reserve_and_finalize
        )
        assert (
            materialized_service_operation_config_api_endpoint.service_operation_config_api_endpoint.id
            == expected_service_operation_config_api_endpoint_id
        )
        assert materialized_service.service.id == expected_service_id

        service_config_head = await FSCommitStore().head(
            branch_id=active_branch_id,
            projection_hash=service_config_projection_hash,
        )
        service_head = await FSCommitStore().head(
            branch_id=active_branch_id,
            projection_hash=service_projection_hash,
        )
        assert (
            service_config_head is not None
            and service_config_head.get("commit_id") is not None
        )
        assert service_head is not None and service_head.get("commit_id") is not None
