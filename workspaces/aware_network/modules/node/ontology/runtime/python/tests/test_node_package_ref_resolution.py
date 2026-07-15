from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from uuid import uuid4

import pytest
from aware_meta.graph.instance.commit.contract import ObjectInstanceGraphCommitRef
from aware_node.package_ref_resolution import (
    NodeRuntimePackageRef,
    NodeRuntimePackageRefReadModel,
    resolve_committed_node_runtime_package_ref,
    resolve_committed_node_runtime_package_refs,
)
from aware_meta.runtime.graph_context import MetaGraphRuntimeIndexSnapshot
from aware_node_ontology.node.node_config import NodeConfig
from aware_node_ontology.node.node_config_environment_target import (
    NodeConfigEnvironmentTarget,
)
from aware_node_ontology.node.node_config_environment_profile_mount import (
    NodeConfigEnvironmentProfileMount,
)
from aware_node_ontology.node.node_config_interface_target import (
    NodeConfigInterfaceTarget,
)
from aware_node_ontology.node.node_config_service_target import (
    NodeConfigServiceTarget,
)
from aware_node_ontology.node.node_package import NodePackage
from aware_node_ontology.node.node_package_included_node_package import (
    NodePackageIncludedNodePackage,
)


@pytest.mark.asyncio
async def test_committed_node_runtime_package_ref_resolves_branchless_oig_pin_without_manifest_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    node_toml = revision_root / "nodes" / "home" / "aware.node.toml"
    _write_revision_manifest(revision_root)

    branch_id = uuid4()
    package_id = uuid4()
    node_config_id = uuid4()
    source_code_package_id = uuid4()
    package_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    node_config_oig_commit_id = uuid4()
    included_package_id = uuid4()
    environment_target_id = uuid4()
    node_config = NodeConfig.model_construct(
        id=node_config_id,
        name="home_story_workspace_node",
        environment_targets=[
            NodeConfigEnvironmentTarget.model_construct(
                id=environment_target_id,
                node_config_id=node_config_id,
                environment_handle="kernel",
                profile_mounts=[
                    NodeConfigEnvironmentProfileMount.model_construct(
                        id=uuid4(),
                        node_config_environment_target_id=environment_target_id,
                        package_name="aware-workspace-environment-profile",
                        profile_key="os.default",
                        mount_key="aware-workspace-environment-profile:os.default",
                        mode="mounted",
                        position=0,
                    )
                ],
            )
        ],
        service_targets=[
            NodeConfigServiceTarget.model_construct(
                id=uuid4(),
                node_config_id=node_config_id,
                service_name="aware_home_devices_service",
            )
        ],
        interface_targets=[
            NodeConfigInterfaceTarget.model_construct(
                id=uuid4(),
                node_config_id=node_config_id,
                interface_name="aware_home_devices",
            )
        ],
    )
    included_bridge = NodePackageIncludedNodePackage.model_construct(
        id=uuid4(),
        node_package_id=package_id,
        included_node_package=None,
        included_node_package_id=included_package_id,
        included_package_name="aware.local_agent_kernel",
        include_key="aware.local_agent_kernel",
    )
    node_package = NodePackage.model_construct(
        id=package_id,
        name="home-story-workspace-node",
        node_config_id=node_config_id,
        node_config=node_config,
        source_code_package_id=source_code_package_id,
        included_node_packages=[included_bridge],
        manifest_relative_path="nodes/home/aware.node.toml",
        fqn_prefix="aware_home_story_workspace_node",
        version_number=7,
        title="Home Story Workspace Node",
        description="Node package ref proof",
        dependencies=[
            {
                "package_name": "aware-home-devices-service",
                "kind": "service_package",
                "version_number": 4,
            }
        ],
    )
    package_ref = NodeRuntimePackageRef(
        family_key="aware_node",
        package_kind="node_package",
        package_name="home-story-workspace-node",
        semantic_package_id=str(package_id),
        semantic_projection_hash="sha256:ExplicitNodePackage",
        semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        semantic_root_kind="node_config",
        semantic_root_id=str(node_config_id),
        semantic_root_object_instance_graph_commit_id=str(node_config_oig_commit_id),
        source_code_package_id=str(source_code_package_id),
    )
    read_model = _static_read_model(
        {
            "NodePackage": "sha256:NodePackage",
            "NodeConfig": "sha256:NodeConfig",
        }
    )

    async def _fake_commit_refs(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["projection_hash"] == "sha256:ExplicitNodePackage"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=branch_id,
                projection_hash="sha256:ExplicitNodePackage",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=package_domain_commit_id,
            ),
        )

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["branch_id"] == branch_id
        assert kwargs["projection_hash"] == "sha256:ExplicitNodePackage"
        assert kwargs["commit_id"] == package_domain_commit_id
        assert kwargs["root_id"] == package_id
        assert kwargs["root_type"] is NodePackage
        assert "hydrate_portal_targets" not in kwargs
        return node_package

    monkeypatch.setattr(
        "aware_node.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_commit_refs,
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.reify_meta_orm_root_from_oig_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_node_runtime_package_ref(
        read_model=read_model,
        package_ref=package_ref,
        materialized_workspace_root=revision_root,
    )

    assert not node_toml.exists()
    assert resolved.manifest_path == node_toml.resolve()
    assert resolved.manifest_relative_path == "nodes/home/aware.node.toml"
    assert resolved.package_name == "home-story-workspace-node"
    assert resolved.node_config_name == "home_story_workspace_node"
    assert resolved.node_package_id == package_id
    assert resolved.node_config_id == node_config_id
    assert resolved.source_code_package_id == source_code_package_id
    assert resolved.semantic_branch_id == str(branch_id)
    assert resolved.semantic_package_id == str(package_id)
    assert resolved.semantic_object_instance_graph_commit_id == str(
        package_oig_commit_id
    )
    assert resolved.semantic_root_object_instance_graph_commit_id == str(
        node_config_oig_commit_id
    )
    assert tuple(dependency.to_payload() for dependency in resolved.dependencies) == (
        {
            "package_name": "aware-home-devices-service",
            "kind": "service_package",
            "version_number": 4,
        },
    )
    assert tuple(
        include.to_payload() for include in resolved.included_node_packages
    ) == (
        {
            "included_package_name": "aware.local_agent_kernel",
            "include_key": "aware.local_agent_kernel",
            "included_node_package_id": str(included_package_id),
        },
    )
    assert tuple(target.to_payload() for target in resolved.environment_targets) == (
        {
            "environment_handle": "kernel",
            "profile_mounts": [
                {
                    "package_name": "aware-workspace-environment-profile",
                    "profile_key": "os.default",
                    "mount_key": "aware-workspace-environment-profile:os.default",
                    "mode": "mounted",
                    "position": 0,
                }
            ],
        },
    )
    assert resolved.service_names == ("aware_home_devices_service",)
    assert resolved.effective_service_names == ("aware_home_devices_service",)
    assert tuple(target.to_payload() for target in resolved.interface_targets) == (
        {"interface_name": "aware_home_devices"},
    )


@pytest.mark.asyncio
async def test_committed_node_runtime_package_ref_defaults_to_meta_runtime_read_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    (revision_root / "modules").mkdir(parents=True)
    _write_revision_manifest(revision_root)

    branch_id = uuid4()
    package_id = uuid4()
    node_config_id = uuid4()
    package_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    node_package = NodePackage.model_construct(
        id=package_id,
        name="home-story-workspace-node",
        node_config_id=node_config_id,
        node_config=NodeConfig.model_construct(
            id=node_config_id,
            name="home_story_workspace_node",
        ),
        manifest_relative_path="nodes/home/aware.node.toml",
    )
    seen_read_model_request: dict[str, object] = {}

    def _fake_read_workspace_meta_runtime_read_model(**kwargs: object) -> object:
        seen_read_model_request.update(kwargs)
        return _static_read_model(
            {
                "NodePackage": "sha256:NodePackage",
                "NodeConfig": "sha256:NodeConfig",
            }
        )

    async def _fake_commit_refs(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["projection_hash"] == "sha256:NodePackage"
        assert kwargs["object_instance_graph_commit_id"] == package_oig_commit_id
        return (
            ObjectInstanceGraphCommitRef(
                branch_id=branch_id,
                projection_hash="sha256:NodePackage",
                object_instance_graph_commit_id=package_oig_commit_id,
                domain_commit_id=package_domain_commit_id,
            ),
        )

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["projection_hash"] == "sha256:NodePackage"
        assert kwargs["commit_id"] == package_domain_commit_id
        assert kwargs["root_id"] == package_id
        return node_package

    monkeypatch.setattr(
        "aware_node.package_ref_resolution.read_workspace_meta_runtime_read_model",
        _fake_read_workspace_meta_runtime_read_model,
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_commit_refs,
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.reify_meta_orm_root_from_oig_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_node_runtime_package_ref(
        package_ref=NodeRuntimePackageRef(
            family_key="aware_node",
            package_kind="node_package",
            package_name="home-story-workspace-node",
            semantic_package_id=str(package_id),
            semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
        ),
        materialized_workspace_root=revision_root,
    )

    assert seen_read_model_request == {
        "repo_root": revision_root.resolve(),
        "aware_root": revision_root.resolve(),
        "required_projection_names": ("NodePackage", "NodeConfig"),
        "composite_name": "Aware Node Package Ref Resolution Read Model",
    }
    assert resolved.package_name == "home-story-workspace-node"
    assert resolved.semantic_branch_id == str(branch_id)


@pytest.mark.asyncio
async def test_committed_node_runtime_package_ref_requires_explicit_repo_root_for_remote_workspace(
    tmp_path: Path,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)

    with pytest.raises(RuntimeError, match="explicit read-model repo_root"):
        await resolve_committed_node_runtime_package_ref(
            package_ref=NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name="home-story-workspace-node",
                semantic_package_id=str(uuid4()),
                semantic_object_instance_graph_commit_id=str(uuid4()),
            ),
            materialized_workspace_root=revision_root,
        )


@pytest.mark.asyncio
async def test_committed_node_runtime_package_refs_resolve_effective_include_closure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    _write_node_toml(revision_root / "nodes" / "home" / "aware.node.toml")
    _write_node_toml(revision_root / "nodes" / "kernel" / "aware.node.toml")

    branch_id = uuid4()
    package_id = uuid4()
    included_package_id = uuid4()
    node_config_id = uuid4()
    included_node_config_id = uuid4()
    package_oig_commit_id = uuid4()
    included_oig_commit_id = uuid4()
    package_domain_commit_id = uuid4()
    included_domain_commit_id = uuid4()

    node_config = NodeConfig.model_construct(
        id=node_config_id,
        name="home_story_workspace_node",
        service_targets=[
            NodeConfigServiceTarget.model_construct(
                id=uuid4(),
                node_config_id=node_config_id,
                service_name="aware_home_devices_service",
            )
        ],
    )
    included_node_config = NodeConfig.model_construct(
        id=included_node_config_id,
        name="aware_local_agent_kernel",
        service_targets=[
            NodeConfigServiceTarget.model_construct(
                id=uuid4(),
                node_config_id=included_node_config_id,
                service_name="aware_meta_service",
            )
        ],
    )
    node_package = NodePackage.model_construct(
        id=package_id,
        name="home-story-workspace-node",
        node_config_id=node_config_id,
        node_config=node_config,
        included_node_packages=[
            NodePackageIncludedNodePackage.model_construct(
                id=uuid4(),
                node_package_id=package_id,
                included_node_package=None,
                included_node_package_id=included_package_id,
                included_package_name="aware.local_agent_kernel",
                include_key="aware.local_agent_kernel",
            )
        ],
        manifest_relative_path="nodes/home/aware.node.toml",
    )
    included_node_package = NodePackage.model_construct(
        id=included_package_id,
        name="aware.local_agent_kernel",
        node_config_id=included_node_config_id,
        node_config=included_node_config,
        manifest_relative_path="nodes/kernel/aware.node.toml",
    )
    refs_by_oig = {
        package_oig_commit_id: ObjectInstanceGraphCommitRef(
            branch_id=branch_id,
            projection_hash="sha256:NodePackage",
            object_instance_graph_commit_id=package_oig_commit_id,
            domain_commit_id=package_domain_commit_id,
        ),
        included_oig_commit_id: ObjectInstanceGraphCommitRef(
            branch_id=branch_id,
            projection_hash="sha256:NodePackage",
            object_instance_graph_commit_id=included_oig_commit_id,
            domain_commit_id=included_domain_commit_id,
        ),
    }

    async def _fake_commit_refs(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self
        assert kwargs["projection_hash"] == "sha256:NodePackage"
        ref = refs_by_oig.get(kwargs["object_instance_graph_commit_id"])
        return (ref,) if ref is not None else ()

    async def _fake_hydrate_root_from_commit(**kwargs: Any) -> object:
        assert kwargs["branch_id"] == branch_id
        assert kwargs["projection_hash"] == "sha256:NodePackage"
        assert kwargs["root_type"] is NodePackage
        assert "hydrate_portal_targets" not in kwargs
        if kwargs["root_id"] == package_id:
            assert kwargs["commit_id"] == package_domain_commit_id
            return node_package
        if kwargs["root_id"] == included_package_id:
            assert kwargs["commit_id"] == included_domain_commit_id
            return included_node_package
        raise AssertionError(f"unexpected root_id={kwargs['root_id']}")

    read_model = _static_read_model(
        {
            "NodePackage": "sha256:NodePackage",
            "NodeConfig": "sha256:NodeConfig",
        }
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _fake_commit_refs,
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.reify_meta_orm_root_from_oig_commit",
        _fake_hydrate_root_from_commit,
    )

    resolved = await resolve_committed_node_runtime_package_refs(
        read_model=read_model,
        package_refs=(
            NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name="home-story-workspace-node",
                semantic_package_id=str(package_id),
                semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
            ),
            NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name="aware.local_agent_kernel",
                semantic_package_id=str(included_package_id),
                semantic_object_instance_graph_commit_id=str(included_oig_commit_id),
            ),
        ),
        materialized_workspace_root=revision_root,
    )

    by_name = {item.package_name: item for item in resolved}
    assert by_name["home-story-workspace-node"].service_names == (
        "aware_home_devices_service",
    )
    assert by_name["home-story-workspace-node"].effective_service_names == (
        "aware_home_devices_service",
        "aware_meta_service",
    )
    assert by_name["aware.local_agent_kernel"].effective_service_names == (
        "aware_meta_service",
    )


@pytest.mark.asyncio
async def test_committed_node_runtime_package_ref_rejects_branchless_legacy_head(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)

    with pytest.raises(
        RuntimeError, match="Branchless Node runtime package refs require"
    ):
        await resolve_committed_node_runtime_package_ref(
            package_ref=NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name="home-story-workspace-node",
                semantic_head_commit_id=str(uuid4()),
            ),
            materialized_workspace_root=revision_root,
        )


@pytest.mark.asyncio
async def test_committed_node_runtime_package_ref_rejects_missing_branchless_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    package_oig_commit_id = uuid4()
    read_model = _static_read_model(
        {
            "NodePackage": "sha256:NodePackage",
            "NodeConfig": "sha256:NodeConfig",
        }
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _async_commit_refs(()),
    )

    with pytest.raises(RuntimeError, match="did not resolve to any indexed"):
        await resolve_committed_node_runtime_package_ref(
            read_model=read_model,
            package_ref=NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name="home-story-workspace-node",
                semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
            ),
            materialized_workspace_root=revision_root,
        )


@pytest.mark.asyncio
async def test_committed_node_runtime_package_ref_rejects_ambiguous_oig_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    revision_root = tmp_path / "revision"
    _write_revision_manifest(revision_root)
    package_oig_commit_id = uuid4()
    read_model = _static_read_model(
        {
            "NodePackage": "sha256:NodePackage",
            "NodeConfig": "sha256:NodeConfig",
        }
    )
    monkeypatch.setattr(
        "aware_node.package_ref_resolution.FSCommitStore."
        "domain_commit_refs_for_object_instance_graph_commit_id",
        _async_commit_refs(
            (
                ObjectInstanceGraphCommitRef(
                    branch_id=uuid4(),
                    projection_hash="sha256:NodePackage",
                    object_instance_graph_commit_id=package_oig_commit_id,
                    domain_commit_id=uuid4(),
                ),
                ObjectInstanceGraphCommitRef(
                    branch_id=uuid4(),
                    projection_hash="sha256:NodePackage",
                    object_instance_graph_commit_id=package_oig_commit_id,
                    domain_commit_id=uuid4(),
                ),
            )
        ),
    )

    with pytest.raises(RuntimeError, match="multiple NodePackage branches"):
        await resolve_committed_node_runtime_package_ref(
            read_model=read_model,
            package_ref=NodeRuntimePackageRef(
                family_key="aware_node",
                package_kind="node_package",
                package_name="home-story-workspace-node",
                semantic_object_instance_graph_commit_id=str(package_oig_commit_id),
            ),
            materialized_workspace_root=revision_root,
        )


def _async_commit_refs(
    refs: tuple[ObjectInstanceGraphCommitRef, ...],
) -> Callable[..., Awaitable[tuple[ObjectInstanceGraphCommitRef, ...]]]:
    async def _fake_commit_refs(
        self: object,
        **kwargs: Any,
    ) -> tuple[ObjectInstanceGraphCommitRef, ...]:
        del self, kwargs
        return refs

    return _fake_commit_refs


def _static_read_model(
    projection_hash_by_name: dict[str, str],
) -> NodeRuntimePackageRefReadModel:
    return cast(
        NodeRuntimePackageRefReadModel,
        cast(
            object,
            SimpleNamespace(
                index=_empty_runtime_index(),
                projection_hash_for_name=lambda projection_name: projection_hash_by_name[
                    projection_name
                ],
            ),
        ),
    )


def _empty_runtime_index() -> MetaGraphRuntimeIndexSnapshot:
    return cast(
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


def _write_revision_manifest(revision_root: Path) -> None:
    manifest = (
        revision_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    )
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")


def _write_node_toml(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("aware_node = 1\n", encoding="utf-8")
