from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, TypeVar
from uuid import UUID, uuid4

from aware_economy.catalog.coins import (
    CoinDeclaration,
    DEFAULT_COIN_DECLARATIONS,
)
from aware_economy.stable_ids import stable_coin_id
from aware_economy_ontology.coin.coin import Coin
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.runtime import (
    MetaGraphRuntime,
    bind_meta_graph_runtime_lane,
    build_meta_graph_runtime_for_aware_package_manifests,
)
from aware_meta.runtime.graph_context import (
    MetaGraphRuntimeContext,
    resolve_meta_runtime_package_manifest_closure_for_package_names,
)
from aware_meta.runtime.handler_executor.contracts import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_root_model
from aware_meta_ontology.graph.projection.object_projection_graph import (
    ObjectProjectionGraph as ObjectProjectionGraphModel,
)
from aware_environment.stable_ids import stable_boot_process_id, stable_boot_thread_id

_DEFAULT_RUNTIME_MODULE_IDS: tuple[str, ...] = (
    "economy",
    "history",
    "environment",
)
_REQUIRED_RUNTIME_MODULE_IDS: tuple[str, ...] = (
    "economy",
    "environment",
)
_TRoot = TypeVar("_TRoot", bound=Coin)


class EconomyMaterializationContext(Protocol):
    @property
    def index(self) -> MetaGraphRuntimeIndex: ...

    @property
    def environment_id(self) -> UUID: ...

    @property
    def process_id(self) -> UUID: ...

    @property
    def thread_id(self) -> UUID: ...

    def bind_lane(
        self,
        *,
        projection: str,
        branch_id: UUID,
    ) -> Any: ...


@dataclass(frozen=True, slots=True)
class _EconomyMaterializationContext:
    runtime: MetaGraphRuntime
    runtime_context: MetaGraphRuntimeContext
    index: MetaGraphRuntimeIndex
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    actor_id: UUID | None = None

    def bind_lane(
        self,
        *,
        projection: str,
        branch_id: UUID,
    ) -> Any:
        return bind_meta_graph_runtime_lane(
            runtime=self.runtime,
            context=self.runtime_context,
            branch_id=branch_id,
            projection=projection,
            actor_id=self.actor_id,
        )


@dataclass(frozen=True, slots=True)
class MaterializedCoinCatalogEntry:
    declaration: CoinDeclaration
    coin: Coin


async def build_default_economy_materialization_context(
    *,
    repo_root: Any | None = None,
    aware_root: Any | None = None,
    actor_id: UUID | None = None,
    environment_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    module_ids: Sequence[str] = _DEFAULT_RUNTIME_MODULE_IDS,
) -> EconomyMaterializationContext:
    if (process_id is None) != (thread_id is None):
        raise ValueError(
            "Economy materialization requires process_id and thread_id together when overriding the default boot lane"
        )

    resolved_repo_root = _require_explicit_path(repo_root, name="repo_root")
    resolved_aware_root = _require_explicit_path(aware_root, name="aware_root")
    resolved_environment_id = environment_id or uuid4()
    return await _build_module_materialization_context(
        repo_root=resolved_repo_root,
        aware_root=resolved_aware_root,
        module_ids=tuple(module_ids),
        actor_id=actor_id,
        environment_id=resolved_environment_id,
        process_id=process_id,
        thread_id=thread_id,
    )


async def ensure_coin_declaration(
    *,
    declaration: CoinDeclaration,
    context: EconomyMaterializationContext | None = None,
    repo_root: Any | None = None,
    aware_root: Any | None = None,
) -> Coin:
    resolved_context = context or await build_default_economy_materialization_context(
        repo_root=repo_root,
        aware_root=aware_root,
    )
    coin_id = stable_coin_id(symbol=declaration.symbol)
    existing = await _materialize_lane_root(
        context=resolved_context,
        root_id=coin_id,
        projection_name="Coin",
        root_type=Coin,
    )
    if existing is not None and _coin_matches(existing, declaration=declaration):
        return existing

    lane = resolved_context.bind_lane(
        projection="Coin",
        branch_id=coin_id,
    )
    with lane.activate(commit=True, publish=False):
        return await Coin.build(
            symbol=declaration.symbol,
            name=declaration.name,
            type=declaration.type,
            decimals=declaration.decimals,
        )


async def ensure_coin_catalog_entries(
    *,
    declarations: Sequence[CoinDeclaration],
    context: EconomyMaterializationContext | None = None,
    repo_root: Any | None = None,
    aware_root: Any | None = None,
) -> tuple[MaterializedCoinCatalogEntry, ...]:
    resolved_context = context or await build_default_economy_materialization_context(
        repo_root=repo_root,
        aware_root=aware_root,
    )
    entries: list[MaterializedCoinCatalogEntry] = []
    seen: set[str] = set()
    for declaration in declarations:
        symbol_key = (declaration.symbol or "").strip().upper()
        if not symbol_key or symbol_key in seen:
            continue
        seen.add(symbol_key)
        coin = await ensure_coin_declaration(
            declaration=declaration,
            context=resolved_context,
        )
        entries.append(
            MaterializedCoinCatalogEntry(
                declaration=declaration,
                coin=coin,
            )
        )
    return tuple(entries)


async def bootstrap_default_coin_catalog(
    *,
    context: EconomyMaterializationContext | None = None,
    repo_root: Any | None = None,
    aware_root: Any | None = None,
) -> tuple[MaterializedCoinCatalogEntry, ...]:
    resolved_context = context or await build_default_economy_materialization_context(
        repo_root=repo_root,
        aware_root=aware_root,
    )
    return await ensure_coin_catalog_entries(
        declarations=DEFAULT_COIN_DECLARATIONS,
        context=resolved_context,
    )


async def _materialize_lane_root(
    *,
    context: EconomyMaterializationContext,
    root_id: UUID,
    projection_name: str,
    root_type: type[_TRoot],
) -> _TRoot | None:
    opg = _resolve_opg_by_name(context.index, name=projection_name)
    head = await FSCommitStore().head(
        branch_id=root_id,
        projection_hash=opg.projection_hash,
    )
    if head is None or head.get("commit_id") is None:
        return None

    oig, _ = await OIGMaterializer().get(
        branch_id=root_id,
        ocg=context.index.ocg,
        opg=opg,
        commit_id=None,
        attribute_configs_by_id=context.index.attribute_configs_by_id,
        class_configs_by_id=context.index.class_configs_by_id,
    )
    root = reify_oig_root_model(
        index=context.index,
        opg=opg,
        oig=oig,
        model_type=root_type,
        root_id=root_id,
        branch_id=root_id,
    )
    if root is None:
        raise RuntimeError(
            "Economy materialization could not hydrate lane root: "
            + f"projection_name={projection_name!r} root_id={root_id}"
        )
    return root


def _resolve_opg_by_name(
    index: MetaGraphRuntimeIndex,
    *,
    name: str,
) -> ObjectProjectionGraphModel:
    matches = [
        opg
        for opg in index.ocg.object_projection_graphs
        if (opg.name or "").strip() == name.strip()
    ]
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one OPG named {name!r}, got {[opg.name for opg in matches]}"
        )
    return matches[0]


async def _build_module_materialization_context(
    *,
    repo_root: Any,
    aware_root: Any,
    module_ids: Sequence[str],
    actor_id: UUID | None,
    environment_id: UUID,
    process_id: UUID | None,
    thread_id: UUID | None,
) -> EconomyMaterializationContext:
    resolved_repo_root = Path(repo_root).expanduser().resolve()
    resolved_aware_root = Path(aware_root).expanduser().resolve()
    runtime_module_ids = _runtime_module_ids(module_ids)
    runtime = build_meta_graph_runtime_for_aware_package_manifests(
        package_manifest_paths=resolve_meta_runtime_package_manifest_closure_for_package_names(
            repo_root=resolved_repo_root,
            package_names=_ontology_package_names(runtime_module_ids),
        ),
        workspace_root=resolved_repo_root,
        aware_root=resolved_aware_root,
        handler_owner_prefixes=_handler_owner_prefixes(runtime_module_ids),
    )
    runtime_context = runtime.context
    if runtime_context is None:
        raise RuntimeError("Economy materialization requires a Meta runtime context.")
    index = runtime_context.index
    boot_process_id, boot_thread_id = _environment_boot_lane_ids(
        environment_id=environment_id,
    )
    return _EconomyMaterializationContext(
        runtime=runtime,
        runtime_context=runtime_context,
        index=index,
        environment_id=environment_id,
        process_id=process_id or boot_process_id,
        thread_id=thread_id or boot_thread_id,
        actor_id=actor_id,
    )


def _environment_boot_lane_ids(*, environment_id: UUID) -> tuple[UUID, UUID]:
    process_id = stable_boot_process_id(environment_id=environment_id)
    thread_id = stable_boot_thread_id(environment_id=environment_id)
    return process_id, thread_id


def _runtime_module_ids(module_ids: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            (
                *(_clean_module_id(module_id) for module_id in module_ids),
                *_REQUIRED_RUNTIME_MODULE_IDS,
            )
        )
    )


def _clean_module_id(module_id: str) -> str:
    token = str(module_id or "").strip().replace("-", "_")
    if not token:
        raise ValueError(
            "Economy materialization module_ids cannot contain empty values."
        )
    return token


def _ontology_package_names(module_ids: Sequence[str]) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            f"{module_id.replace('_', '-')}-ontology" for module_id in module_ids
        )
    )


def _handler_owner_prefixes(module_ids: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(f"aware_{module_id}" for module_id in module_ids))


def _require_explicit_path(value: Any | None, *, name: str) -> Path:
    if value is None:
        raise ValueError(
            "Economy materialization requires an explicit "
            + f"{name}; pass a context or provide {name}=..."
        )
    return Path(value).expanduser().resolve()


def _coin_matches(coin: Coin, *, declaration: CoinDeclaration) -> bool:
    return (
        (coin.symbol or "").strip().upper() == declaration.symbol.strip().upper()
        and (coin.name or "").strip() == declaration.name.strip()
        and coin.type == declaration.type
        and coin.decimals == declaration.decimals
    )


__all__ = [
    "EconomyMaterializationContext",
    "MaterializedCoinCatalogEntry",
    "bootstrap_default_coin_catalog",
    "build_default_economy_materialization_context",
    "ensure_coin_catalog_entries",
    "ensure_coin_declaration",
]
