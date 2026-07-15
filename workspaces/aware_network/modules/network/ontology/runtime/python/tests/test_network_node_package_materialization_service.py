from __future__ import annotations

from pathlib import Path
from typing import TypeVar
from uuid import UUID, uuid4

import pytest

from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_package_config_id,
    stable_code_package_id,
)
from aware_code_ontology.package.code_package import CodePackage
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.fs_snapshot_store import FSSnapshotStore
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_meta.runtime.oig_hydration import reify_meta_orm_root_from_oig_commit
from aware_network_ontology.network.network_node_config import NetworkNodeConfig
from aware_network_ontology.network.network_node_package import NetworkNodePackage
from aware_network_ontology.stable_ids import (
    stable_network_node_config_id,
    stable_network_node_package_id,
)
from aware_orm.models.orm_model import ORMModel

_TRoot = TypeVar("_TRoot", bound=ORMModel)
REPO_ROOT = Path(__file__).resolve().parents[8]


def _source_code_package_config_id() -> UUID:
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface="runtime",
        )
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_node_package_fixture(*, workspace_root: Path) -> Path:
    node_toml_path = workspace_root / "aware.node.toml"
    _write(
        node_toml_path,
        "\n".join(
            [
                "aware_node = 1",
                "",
                "[node]",
                'package_name = "kernel-node"',
                'fqn_prefix = "aware_kernel_node"',
                'title = "Kernel Node"',
                'description = "Canonical node package for package materialization tests"',
                "",
                "[build]",
                'sources_dir = "nodes"',
                'include_paths = ["**/*.aware"]',
                'compilation_mode = "node_ontology"',
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "nodes" / "kernel_node.aware",
        "\n".join(
            [
                "class KernelNodeManifest {",
                "    name String",
                "}",
                "",
            ]
        ),
    )
    return node_toml_path


async def _rehydrate_projection_root(
    *,
    index: MetaGraphRuntimeIndexSnapshot,
    branch_id: UUID,
    projection_hash: str,
    projection_name: str,
    root_id: UUID,
    root_type: type[_TRoot],
) -> _TRoot:
    commit_store = FSCommitStore()
    head = await commit_store.head(
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    assert head is not None
    assert head.get("commit_id") is not None
    root = await reify_meta_orm_root_from_oig_commit(
        index=index,
        branch_id=branch_id,
        projection_hash=projection_hash,
        projection_name=projection_name,
        commit_id=UUID(str(head["commit_id"])),
        root_id=root_id,
        root_type=root_type,
        commit_store=commit_store,
        snapshot_store=FSSnapshotStore(),
    )
    assert root is not None
    return root


def _install_isolated_aware_root(
    monkeypatch: pytest.MonkeyPatch,
    aware_root: Path,
) -> Path:
    resolved = aware_root.expanduser().resolve()
    resolved.mkdir(parents=True, exist_ok=True)
    (resolved / ".aware").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("AWARE_ROOT", str(resolved))
    monkeypatch.setenv("AWARE_PERSISTENCE_BACKEND", "fs")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return resolved


@pytest.mark.asyncio
async def test_materialize_network_node_package_from_manifest_commits_canonical_package_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace_root = tmp_path / "network_node_package_materialization"
    workspace_root.mkdir(parents=True, exist_ok=True)
    node_toml_path = _write_node_package_fixture(workspace_root=workspace_root)

    monkeypatch.syspath_prepend(str(REPO_ROOT / "modules" / "network" / "runtime"))
    _install_isolated_aware_root(
        monkeypatch,
        tmp_path / "aware_root_network_node_package_materialization",
    )

    from aware_network.materialization import (  # noqa: WPS433
        materialize_network_node_package_from_manifest,
        resolve_network_node_package_materialization_spec,
    )
    from aware_network.materialization import service as network_service  # noqa: WPS433

    spec = resolve_network_node_package_materialization_spec(
        node_toml_path=node_toml_path,
        workspace_root=workspace_root,
    )
    assert spec.package_name == "kernel-node"
    assert spec.package_fqn_prefix == "aware_kernel_node"
    assert spec.config_name == "kernel-node"
    assert (
        spec.config_description
        == "Canonical node package for package materialization tests"
    )
    assert spec.source_files == ("nodes/kernel_node.aware",)

    read_model = (
        network_service._resolve_network_node_package_materialization_read_model(
            workspace_root=workspace_root,
            repo_root=REPO_ROOT,
        )
    )
    index = read_model.index

    environment_id = uuid4()
    process_id = uuid4()
    thread_id = uuid4()
    branch_id = uuid4()

    code_package_projection_hash = read_model.projection_hash_for_name("CodePackage")
    network_node_config_projection_hash = read_model.projection_hash_for_name(
        "NetworkNodeConfig"
    )
    network_node_package_projection_hash = read_model.projection_hash_for_name(
        "NetworkNodePackage"
    )
    assert code_package_projection_hash
    assert network_node_config_projection_hash
    assert network_node_package_projection_hash

    result = await materialize_network_node_package_from_manifest(
        runtime=None,
        index=None,
        actor_id=None,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        workspace_root=workspace_root,
        node_toml_path=node_toml_path,
        repo_root=REPO_ROOT,
    )

    expected_source_code_package_id = stable_code_package_id(
        code_package_config_id=_source_code_package_config_id(),
        package_name="kernel-node",
        language="aware",
    )
    expected_network_node_config_id = stable_network_node_config_id(
        name="kernel-node",
    )
    expected_network_node_package_id = stable_network_node_package_id(
        name="kernel-node"
    )

    assert result.node_toml_path == node_toml_path.resolve()
    assert result.workspace_root == workspace_root.resolve()
    assert result.manifest_spec.node.package_name == "kernel-node"
    assert result.network_node_config.id == expected_network_node_config_id
    assert result.network_node_package.id == expected_network_node_package_id
    assert (
        result.network_node_package.network_node_config_id
        == expected_network_node_config_id
    )
    assert result.source_files == ("nodes/kernel_node.aware",)
    assert result.source_code_package_id == expected_source_code_package_id
    assert result.network_node_config_commit_id is not None
    assert result.network_node_config_head_commit_id is not None
    assert result.package_commit_id is not None
    assert result.package_head_commit_id is not None

    code_package = await _rehydrate_projection_root(
        index=index,
        branch_id=branch_id,
        projection_hash=code_package_projection_hash,
        projection_name="CodePackage",
        root_id=expected_source_code_package_id,
        root_type=CodePackage,
    )
    assert code_package.package_name == "kernel-node"
    assert code_package.code_package_config_id == _source_code_package_config_id()
    assert code_package.surface == "runtime"
    assert code_package.manifest_relative_path == "aware.node.toml"
    assert code_package.package_root == "."
    assert code_package.sources_root == "nodes"
    assert code_package.fqn_prefix == "aware_kernel_node"
    assert {edge.relative_path for edge in code_package.code_package_codes} == {
        "nodes/kernel_node.aware"
    }

    network_node_config = await _rehydrate_projection_root(
        index=index,
        branch_id=branch_id,
        projection_hash=network_node_config_projection_hash,
        projection_name="NetworkNodeConfig",
        root_id=expected_network_node_config_id,
        root_type=NetworkNodeConfig,
    )
    assert network_node_config.name == "kernel-node"
    assert (
        network_node_config.description
        == "Canonical node package for package materialization tests"
    )

    network_node_package = await _rehydrate_projection_root(
        index=index,
        branch_id=branch_id,
        projection_hash=network_node_package_projection_hash,
        projection_name="NetworkNodePackage",
        root_id=expected_network_node_package_id,
        root_type=NetworkNodePackage,
    )
    assert network_node_package.name == "kernel-node"
    assert (
        network_node_package.network_node_config_id == expected_network_node_config_id
    )
    assert (
        network_node_package.source_code_package_id == expected_source_code_package_id
    )


def test_network_node_package_materialization_read_model_requires_explicit_repo_root_for_remote_workspace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.syspath_prepend(str(REPO_ROOT / "modules" / "network" / "runtime"))
    _install_isolated_aware_root(
        monkeypatch,
        tmp_path / "aware_root_network_node_package_materialization",
    )
    from aware_network.materialization import service as network_service  # noqa: WPS433

    with pytest.raises(RuntimeError, match="requires an explicit read-model repo_root"):
        network_service._resolve_network_node_package_materialization_read_model(
            workspace_root=tmp_path / "remote_workspace",
        )
