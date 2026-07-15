from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID, uuid4

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[8]
for _path in (
    _REPO_ROOT,
    _REPO_ROOT / "workspaces" / "aware_network" / "modules" / "interface" / "ontology" / "runtime" / "python",
):
    _path_str = str(_path.resolve())
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

from aware_interface.package_ref_resolution import (  # noqa: E402
    InterfaceRuntimePackageRef,
    resolve_committed_interface_runtime_package_ref,
)
from aware_interface_ontology.interface.interface_config import InterfaceConfig  # noqa: E402
from aware_interface_ontology.interface.interface_package import InterfacePackage  # noqa: E402
from aware_meta_ontology.graph.instance.object_instance_graph_commit import (  # noqa: E402
    ObjectInstanceGraphCommit,
)
from aware_meta.runtime import MetaGraphRuntimeIndexSnapshot  # noqa: E402


@pytest.mark.asyncio
async def test_committed_interface_runtime_package_ref_hydrates_package_and_interface_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware_root"))
    interface_toml = revision_root / "interfaces" / "control_plane" / "aware.interface.toml"
    _write_revision_manifest(revision_root)
    interface_toml.parent.mkdir(parents=True, exist_ok=True)
    interface_toml.write_text("aware_interface = 1\n", encoding="utf-8")

    branch_id = uuid4()
    package_id = uuid4()
    interface_config_id = uuid4()
    package_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    interface_config_oig_commit_id = uuid4()
    interface_config_domain_commit_id = uuid4()
    source_code_package_id = uuid4()

    interface_config_commit = ObjectInstanceGraphCommit.model_construct(
        id=interface_config_oig_commit_id,
        commit_id=interface_config_domain_commit_id,
    )
    interface_config = InterfaceConfig.model_construct(
        id=interface_config_id,
        name="aware-control-plane",
    )
    interface_package = InterfacePackage.model_construct(
        id=package_id,
        name="aware-control-plane-interface",
        interface_config_id=interface_config_id,
        interface_config=interface_config,
        interface_config_object_instance_graph_commit_id=(interface_config_oig_commit_id),
        interface_config_object_instance_graph_commit=interface_config_commit,
        source_code_package_id=source_code_package_id,
        manifest_relative_path="interfaces/control_plane/aware.interface.toml",
        fqn_prefix="aware_control_plane_interface",
        config_bundle_path="interfaces/control_plane/bundles/interface.config.bundle.json",
    )
    package_ref = InterfaceRuntimePackageRef(
        family_key="interface",
        package_kind="interface",
        package_name="aware-control-plane-interface",
        semantic_package_id=str(package_id),
        semantic_head_commit_id=str(package_oig_commit_id),
        semantic_branch_id=str(branch_id),
        semantic_root_kind="interface_config",
        semantic_root_id=str(interface_config_id),
        semantic_root_object_instance_graph_commit_id=str(interface_config_oig_commit_id),
    )
    index = cast(
        MetaGraphRuntimeIndexSnapshot,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    def _fake_projection_hash(*, index: MetaGraphRuntimeIndexSnapshot, projection_name: str) -> str:
        del index
        return f"sha256:{projection_name}"

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self
        assert kwargs["branch_id"] == branch_id
        assert kwargs["projection_hash"] == "sha256:InterfacePackage"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return package_domain_commit_id

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        if kwargs["root_type"] is InterfacePackage:
            assert kwargs["projection_hash"] == "sha256:InterfacePackage"
            assert kwargs["commit_id"] == package_domain_commit_id
            assert kwargs["root_id"] == package_id
            return interface_package
        assert kwargs["root_type"] is InterfaceConfig
        assert kwargs["projection_hash"] == "sha256:InterfaceConfig"
        assert kwargs["commit_id"] == interface_config_domain_commit_id
        assert kwargs["root_id"] == interface_config_id
        return interface_config

    monkeypatch.setattr(
        "aware_interface.package_ref_resolution.find_meta_graph_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_interface.package_ref_resolution.FSCommitStore." "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_interface.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_interface_runtime_package_ref(
        index=index,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
    )

    assert resolved.interface_package_id == package_id
    assert resolved.interface_config_id == interface_config_id
    assert resolved.interface_config_object_instance_graph_commit_id == interface_config_oig_commit_id
    assert resolved.manifest_path == interface_toml.resolve()
    assert resolved.manifest_relative_path == ("interfaces/control_plane/aware.interface.toml")
    assert resolved.package_name == "aware-control-plane-interface"
    assert resolved.fqn_prefix == "aware_control_plane_interface"
    assert resolved.config_bundle_path == ("interfaces/control_plane/bundles/interface.config.bundle.json")
    assert resolved.semantic_package_id == str(package_id)
    assert resolved.semantic_root_object_instance_graph_commit_id == str(interface_config_oig_commit_id)
    assert resolved.source_code_package_id == str(source_code_package_id)
    assert resolved.interface_package is interface_package
    assert resolved.interface_config is interface_config


@pytest.mark.asyncio
async def test_committed_interface_runtime_package_ref_rejects_root_pin_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    monkeypatch.setenv("AWARE_ROOT", str(tmp_path / "aware_root"))
    interface_toml = revision_root / "interfaces" / "app" / "aware.interface.toml"
    _write_revision_manifest(revision_root)
    interface_toml.parent.mkdir(parents=True, exist_ok=True)
    interface_toml.write_text("aware_interface = 1\n", encoding="utf-8")

    branch_id = uuid4()
    package_id = uuid4()
    interface_config_id = uuid4()
    package_oig_commit_id = uuid4()
    interface_config_oig_commit_id = uuid4()
    interface_package = InterfacePackage.model_construct(
        id=package_id,
        name="aware-app-interface",
        interface_config_id=interface_config_id,
        interface_config_object_instance_graph_commit_id=(interface_config_oig_commit_id),
        manifest_relative_path="interfaces/app/aware.interface.toml",
    )
    package_ref = InterfaceRuntimePackageRef(
        family_key="interface",
        package_kind="interface",
        package_name="aware-app-interface",
        semantic_package_id=str(package_id),
        semantic_head_commit_id=str(package_oig_commit_id),
        semantic_branch_id=str(branch_id),
        semantic_root_kind="interface_config",
        semantic_root_id=str(interface_config_id),
        semantic_root_object_instance_graph_commit_id=str(uuid4()),
    )
    index = cast(
        MetaGraphRuntimeIndexSnapshot,
        cast(
            object,
            SimpleNamespace(
                opg_by_hash={},
                ocg=object(),
                attribute_configs_by_id={},
                class_configs_by_id={},
            ),
        ),
    )

    def _fake_projection_hash(*, index: MetaGraphRuntimeIndexSnapshot, projection_name: str) -> str:
        del index
        return f"sha256:{projection_name}"

    async def _fake_domain_commit_id_for_oig_commit_id(
        self: object,
        **kwargs: Any,
    ) -> UUID:
        del self, kwargs
        return uuid4()

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["root_type"] is InterfacePackage
        return interface_package

    monkeypatch.setattr(
        "aware_interface.package_ref_resolution.find_meta_graph_projection_hash_by_name",
        _fake_projection_hash,
    )
    monkeypatch.setattr(
        "aware_interface.package_ref_resolution.FSCommitStore." "domain_commit_id_for_object_instance_graph_commit_id",
        _fake_domain_commit_id_for_oig_commit_id,
    )
    monkeypatch.setattr(
        "aware_interface.package_ref_resolution._hydrate_root_from_commit",
        _fake_hydrate_root_from_commit,
    )

    with pytest.raises(
        RuntimeError,
        match="semantic_root_object_instance_graph_commit_id",
    ):
        await resolve_committed_interface_runtime_package_ref(
            index=index,
            package_ref=package_ref,
            materialized_workspace_root=revision_root,
        )


def _write_revision_manifest(root: Path) -> None:
    manifest_path = root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text('{"version": 1}\n', encoding="utf-8")
