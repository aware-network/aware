from __future__ import annotations

from uuid import uuid4

import pytest

from aware_network.network.node.local_info import (
    LocalNetworkNodeInfo,
    normalize_local_network_node_info_identity,
)
from aware_network.network.node.manager import NetworkNodeManager
from aware_network_ontology.stable_ids import stable_network_node_id
from aware_node_operator.operator_identity import stable_operator_node_identity


def test_normalize_local_network_node_info_fills_dev_public_key_and_stable_id() -> None:
    legacy_id = uuid4()
    info = LocalNetworkNodeInfo(id=legacy_id, public_key=None)

    normalized = normalize_local_network_node_info_identity(info)

    assert normalized.public_key == f"dev:node:{legacy_id}"
    assert normalized.id == stable_network_node_id(public_key=normalized.public_key)


def test_normalize_local_network_node_info_preserves_consistent_identity() -> None:
    public_key = "dev:node:test-kernel"
    node_id = stable_network_node_id(public_key=public_key)
    info = LocalNetworkNodeInfo(id=node_id, public_key=public_key)

    assert normalize_local_network_node_info_identity(info) is info


def test_workspace_operator_identity_is_network_node_identity_stable() -> None:
    identity = stable_operator_node_identity(
        workspace_revision_id=uuid4(),
        node_package="aware-network-environment-node",
    )
    info = LocalNetworkNodeInfo(
        id=identity.node_id,
        public_key=identity.public_key,
    )

    assert normalize_local_network_node_info_identity(info) is info


def test_network_node_manager_requires_explicit_node_info_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_NODE_INFO_PATH", raising=False)
    for env_var in NetworkNodeManager._NODE_INFO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)

    with pytest.raises(RuntimeError, match="requires AWARE_NODE_INFO_PATH"):
        NetworkNodeManager._get_node_info_path()


def test_network_node_manager_resolves_explicit_state_root(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_NODE_INFO_PATH", raising=False)
    for env_var in NetworkNodeManager._NODE_INFO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.setenv("AWARE_NETWORK_NODE_INFO_ROOT", str(tmp_path))

    path = NetworkNodeManager._get_node_info_path()

    assert path == tmp_path.resolve() / ".aware" / "network_node.json"
    assert path.parent.is_dir()


def test_network_node_manager_saves_and_loads_explicit_node_info_path(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    node_info_path = tmp_path / "node-state" / "network_node.json"
    monkeypatch.setenv("AWARE_NODE_INFO_PATH", str(node_info_path))
    for env_var in NetworkNodeManager._NODE_INFO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    info = LocalNetworkNodeInfo(public_key="dev:node:explicit")

    NetworkNodeManager.save_local_info(info)
    loaded = NetworkNodeManager.load_local_info()

    assert node_info_path.exists()
    assert loaded is not None
    assert loaded.public_key == "dev:node:explicit"
