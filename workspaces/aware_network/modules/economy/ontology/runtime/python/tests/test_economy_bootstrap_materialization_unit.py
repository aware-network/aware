from __future__ import annotations

import ast
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from ._economy_runtime_test_paths import REPO_ROOT
import aware_economy
from aware_economy.stable_ids import stable_coin_id
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.runtime.author import META_SYSTEM_ACTOR_ID
from aware_meta.runtime.testing import IsolatedMetaAwareRoot
from aware_environment.stable_ids import stable_boot_process_id, stable_boot_thread_id


_BOOTSTRAP_SOURCE = (
    Path(aware_economy.__file__).resolve().parent
    / "ontology"
    / "materialization"
    / "bootstrap.py"
)


def _projection_hash(index, name: str) -> str:  # noqa: ANN001 - test helper
    matches = [
        opg.projection_hash
        for opg in index.ocg.object_projection_graphs
        if (opg.name or "").strip() == name
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"Expected one projection hash for {name!r}, got {matches}"
        )
    return matches[0]


async def _head_commit_id(
    store: FSCommitStore, *, branch_id: UUID, projection_hash: str
) -> UUID:
    head = await store.head(branch_id=branch_id, projection_hash=projection_hash)
    assert head and head.get(
        "commit_id"
    ), f"Missing lane head: branch_id={branch_id} projection={projection_hash}"
    return UUID(str(head["commit_id"]))


def _import_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


async def _build_context_or_xfail(
    build_default_economy_materialization_context,  # noqa: ANN001 - imported helper is duck typed
    *,
    aware_root: Path,
    environment_id: UUID,
) -> object:
    return await build_default_economy_materialization_context(
        repo_root=REPO_ROOT,
        aware_root=aware_root,
        actor_id=META_SYSTEM_ACTOR_ID,
        environment_id=environment_id,
    )


def test_economy_bootstrap_materialization_has_no_direct_runtime_imports() -> None:
    assert "aware_runtime" not in _BOOTSTRAP_SOURCE.read_text(encoding="utf-8")
    assert "aware_runtime" not in _import_roots(_BOOTSTRAP_SOURCE)


@pytest.mark.asyncio
async def test_economy_bootstrap_materialization_is_idempotent(tmp_path: Path) -> None:
    from aware_economy.catalog.coins import DEFAULT_COIN_DECLARATIONS
    from aware_economy.ontology.materialization import (
        bootstrap_default_coin_catalog,
        build_default_economy_materialization_context,
    )

    aware_root = tmp_path / "aware_root"
    with IsolatedMetaAwareRoot(aware_root, persistence_backend="fs"):
        context = await _build_context_or_xfail(
            build_default_economy_materialization_context,
            aware_root=aware_root,
            environment_id=uuid4(),
        )
        index = context.index
        environment_id = context.environment_id
        assert context.process_id == stable_boot_process_id(
            environment_id=environment_id
        )
        assert context.thread_id == stable_boot_thread_id(environment_id=environment_id)

        store = FSCommitStore()
        first_entries = await bootstrap_default_coin_catalog(context=context)
        first_by_symbol = {entry.coin.symbol: entry.coin for entry in first_entries}
        assert {"AWC", "USD"}.issubset(first_by_symbol)

        coin_projection_hash = _projection_hash(index, "Coin")
        heads_before = {
            declaration.symbol: await _head_commit_id(
                store,
                branch_id=stable_coin_id(symbol=declaration.symbol),
                projection_hash=coin_projection_hash,
            )
            for declaration in DEFAULT_COIN_DECLARATIONS
        }

        second_entries = await bootstrap_default_coin_catalog(context=context)
        second_by_symbol = {entry.coin.symbol: entry.coin for entry in second_entries}
        assert set(second_by_symbol) == set(heads_before)
        assert second_by_symbol["USD"].id == stable_coin_id(symbol="USD")
        assert second_by_symbol["AWC"].id == stable_coin_id(symbol="AWC")

        heads_after = {
            declaration.symbol: await _head_commit_id(
                store,
                branch_id=stable_coin_id(symbol=declaration.symbol),
                projection_hash=coin_projection_hash,
            )
            for declaration in DEFAULT_COIN_DECLARATIONS
        }
        assert heads_after == heads_before


@pytest.mark.asyncio
async def test_economy_bootstrap_shim_materializes_required_default_coins(
    tmp_path: Path,
) -> None:
    from aware_economy.bootstrap import bootstrap_economy
    from aware_economy.ontology.materialization import (
        build_default_economy_materialization_context,
    )

    aware_root = tmp_path / "aware_root"
    with IsolatedMetaAwareRoot(aware_root, persistence_backend="fs"):
        context = await _build_context_or_xfail(
            build_default_economy_materialization_context,
            aware_root=aware_root,
            environment_id=uuid4(),
        )
        entries = await bootstrap_economy(context=context)
        by_symbol = {entry.coin.symbol: entry.coin for entry in entries}

        assert by_symbol["USD"].id == stable_coin_id(symbol="USD")
        assert by_symbol["AWC"].id == stable_coin_id(symbol="AWC")
