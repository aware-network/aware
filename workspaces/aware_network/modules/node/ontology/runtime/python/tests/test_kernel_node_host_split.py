from __future__ import annotations

from pathlib import Path
import sys
import tomllib

_REPO_ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "aware.repo.toml").is_file()
)
_REPO_ROOT_STR = str(_REPO_ROOT)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)
_NODE_RUNTIME_ROOT_STR = str(_REPO_ROOT / "modules" / "node" / "runtime")
if _NODE_RUNTIME_ROOT_STR not in sys.path:
    sys.path.insert(0, _NODE_RUNTIME_ROOT_STR)

from aware_node.manifest.spec import AwareNodeDependencyKind  # noqa: E402
from aware_node.compile import NodeCompilePlan, compile_node_workspace  # noqa: E402


def _compile_kernel_node(relpath: str) -> NodeCompilePlan:
    result = compile_node_workspace(
        toml_path=_REPO_ROOT / relpath,
        repo_root=_REPO_ROOT,
        emit_compile_plan=False,
    )
    assert result.compile_plan is not None
    return result.compile_plan


def _dependency_pairs(relpath: str) -> tuple[tuple[str, str], ...]:
    result = compile_node_workspace(
        toml_path=_REPO_ROOT / relpath,
        repo_root=_REPO_ROOT,
        emit_compile_plan=False,
    )
    return tuple(
        (dependency.package_name, dependency.kind.value)
        for dependency in result.snapshot.spec.dependencies
    )


def test_kernel_environment_host_owns_only_environment_and_meta_authority() -> None:
    plan = _compile_kernel_node("nodes/kernel_environment_host/aware.node.toml")

    assert plan.package_name == "kernel-environment-node"
    assert plan.node_ownership.name == "kernel_environment_host"
    assert tuple(
        target.environment_handle for target in plan.node_ownership.environment_targets
    ) == ("aware-kernel-runtime",)
    assert tuple(
        (
            mount.package_name,
            mount.profile_key,
            mount.mount_key,
            mount.mode,
            mount.position,
        )
        for target in plan.node_ownership.environment_targets
        for mount in target.profile_mounts
    ) == (
        (
            "aware-control-environment-profile",
            "control.default",
            "aware-control-environment-profile:control.default",
            "mounted",
            0,
        ),
    )
    assert tuple(
        target.service_name for target in plan.node_ownership.service_targets
    ) == (
        "aware_environment",
        "aware_meta",
    )
    assert plan.node_ownership.interface_targets == ()

    global_services = {
        "aware_identity",
        "aware_economy",
        "aware_attention",
        "aware_experience",
    }
    assert global_services.isdisjoint(
        {target.service_name for target in plan.node_ownership.service_targets}
    )
    assert all(
        kind != AwareNodeDependencyKind.experience_package.value
        for _package_name, kind in _dependency_pairs(
            "nodes/kernel_environment_host/aware.node.toml"
        )
    )


def test_kernel_hosts_do_not_depend_on_workspace_product_packages() -> None:
    workspace_product_packages = {
        "aware-workspace",
        "aware-workspace-interface",
        "aware-workspace-service",
        "aware-conversation-service",
        "aware-issue-service",
        "aware-feed-service",
    }

    for node_toml in (
        "nodes/kernel_environment_host/aware.node.toml",
        "nodes/kernel_services_host/aware.node.toml",
        "nodes/kernel_interface_host/aware.node.toml",
    ):
        assert workspace_product_packages.isdisjoint(
            {package_name for package_name, _kind in _dependency_pairs(node_toml)}
        )


def test_kernel_services_host_owns_only_shared_global_services() -> None:
    plan = _compile_kernel_node("nodes/kernel_services_host/aware.node.toml")

    assert plan.package_name == "kernel-services-node"
    assert plan.node_ownership.name == "kernel_services_host"
    assert plan.node_ownership.environment_targets == ()
    assert plan.node_ownership.interface_targets == ()
    assert tuple(
        target.service_name for target in plan.node_ownership.service_targets
    ) == (
        "aware_attention",
        "aware_economy",
        "aware_experience",
        "aware_hub",
        "aware_identity",
        "aware_network",
        "aware_reactivity",
    )
    assert set(_dependency_pairs("nodes/kernel_services_host/aware.node.toml")) == {
        ("aware-attention-service", AwareNodeDependencyKind.service_package.value),
        ("aware-economy-service", AwareNodeDependencyKind.service_package.value),
        ("aware-experience-service", AwareNodeDependencyKind.service_package.value),
        ("aware-hub-service", AwareNodeDependencyKind.service_package.value),
        ("aware-identity-service", AwareNodeDependencyKind.service_package.value),
        ("aware-network-service", AwareNodeDependencyKind.service_package.value),
        ("aware-reactivity-service", AwareNodeDependencyKind.service_package.value),
    }


def test_kernel_service_provider_sets_are_declared_by_service_contracts() -> None:
    global_service_tomls = (
        "workspaces/aware_network/modules/attention/services/attention/aware.service.toml",
        "workspaces/aware_network/modules/economy/services/economy/aware.service.toml",
        "workspaces/aware_network/modules/experience/services/experience/aware.service.toml",
        "workspaces/aware_network/modules/hub/services/hub/aware.service.toml",
        "workspaces/aware_network/modules/identity/services/identity/aware.service.toml",
        "workspaces/aware_network/modules/network/services/network/aware.service.toml",
        "workspaces/aware_network/modules/reactivity/services/reactivity/aware.service.toml",
    )
    for relpath in global_service_tomls:
        payload = tomllib.loads((_REPO_ROOT / relpath).read_text(encoding="utf-8"))
        assert payload["api_provider_sets"] == [
            {
                "key": "kernel.global_services.v1",
                "title": "Kernel Global Services",
                "membership_key": "kernel-services-host",
                "description": "Kernel global service providers.",
            }
        ]
        assert (
            payload["implementation"]["packages"][0]["package_name"]
            == payload["service"]["package_name"]
        )

    environment_authority_tomls = (
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
        "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
    )
    for relpath in environment_authority_tomls:
        payload = tomllib.loads((_REPO_ROOT / relpath).read_text(encoding="utf-8"))
        assert payload["api_provider_sets"] == [
            {
                "key": "kernel.environment_authority.v1",
                "title": "Kernel Environment Authority",
                "membership_key": "kernel-environment-host",
                "description": "Kernel environment and Meta authority service providers.",
            }
        ]
        assert (
            payload["implementation"]["packages"][0]["package_name"]
            == payload["service"]["package_name"]
        )


def test_kernel_interface_host_owns_only_control_interface() -> None:
    plan = _compile_kernel_node("nodes/kernel_interface_host/aware.node.toml")

    assert plan.package_name == "kernel-interface-node"
    assert plan.node_ownership.name == "kernel_interface_host"
    assert plan.node_ownership.environment_targets == ()
    assert plan.node_ownership.service_targets == ()
    assert tuple(
        target.interface_name for target in plan.node_ownership.interface_targets
    ) == ("aware_control",)
    assert _dependency_pairs("nodes/kernel_interface_host/aware.node.toml") == (
        ("aware-control-interface", AwareNodeDependencyKind.interface_package.value),
    )


def test_workspace_environment_host_owns_product_environment_profile() -> None:
    workspace_environment_host_toml = "workspaces/aware_workspace/modules/workspace/nodes/workspace_environment_host/aware.node.toml"
    plan = _compile_kernel_node(workspace_environment_host_toml)

    assert plan.package_name == "workspace-environment-node"
    assert plan.node_ownership.name == "workspace_environment_host"
    assert tuple(
        target.environment_handle for target in plan.node_ownership.environment_targets
    ) == ("workspace",)
    assert tuple(
        (
            mount.package_name,
            mount.profile_key,
            mount.mount_key,
            mount.mode,
            mount.position,
        )
        for target in plan.node_ownership.environment_targets
        for mount in target.profile_mounts
    ) == (
        (
            "aware-workspace-environment-profile",
            "os.default",
            "aware-workspace-environment-profile:os.default",
            "mounted",
            0,
        ),
    )
    assert tuple(
        target.service_name for target in plan.node_ownership.service_targets
    ) == (
        "aware_environment",
        "aware_meta",
    )
    assert plan.node_ownership.interface_targets == ()
    assert set(_dependency_pairs(workspace_environment_host_toml)) == {
        ("aware-environment-service", AwareNodeDependencyKind.service_package.value),
        ("aware-meta-service", AwareNodeDependencyKind.service_package.value),
    }


def test_workspace_services_host_owns_only_product_services() -> None:
    workspace_services_host_toml = "workspaces/aware_workspace/modules/workspace/nodes/workspace_services_host/aware.node.toml"
    plan = _compile_kernel_node(workspace_services_host_toml)

    assert plan.package_name == "workspace-services-node"
    assert plan.node_ownership.name == "workspace_services_host"
    assert plan.node_ownership.environment_targets == ()
    assert plan.node_ownership.interface_targets == ()
    assert tuple(
        target.service_name for target in plan.node_ownership.service_targets
    ) == ("aware_workspace",)
    assert set(_dependency_pairs(workspace_services_host_toml)) == {
        ("aware-workspace-service", AwareNodeDependencyKind.service_package.value),
    }


def test_workspace_product_views_are_canonical_workspace_refs() -> None:
    workspace_root = (
        _REPO_ROOT / "workspaces" / "aware_workspace" / "modules" / "workspace"
    )
    interface_source = (
        workspace_root / "interfaces" / "aware_workspace" / "aware_workspace.aware"
    ).read_text(encoding="utf-8")
    profile_source = (
        workspace_root / "experiences" / "aware-workspace" / "profiles.aware"
    ).read_text(encoding="utf-8")
    workspace_experience_source = (
        workspace_root / "experiences" / "aware-workspace" / "experiences.aware"
    ).read_text(encoding="utf-8")
    interface_toml = tomllib.loads(
        (
            workspace_root / "interfaces" / "aware_workspace" / "aware.interface.toml"
        ).read_text(encoding="utf-8")
    )

    assert "api conversation" not in interface_source
    assert "api feed" not in interface_source
    assert "api issue" not in interface_source
    assert "mount main.ide_workbench.primary" in interface_source
    assert "mount main.ide_workbench.orchestration" in interface_source
    assert "mount main.ide_workbench.primary" in interface_source

    assert "projection aware_workspace view control.main" in profile_source
    assert "layout ide_workbench default" in profile_source
    assert "projection aware_conversations" not in profile_source
    assert "projection aware_issues" not in profile_source
    assert "projection aware_feeds" not in profile_source

    assert "aware_workflow.issue.Issue" not in workspace_experience_source
    assert (
        "aware_conversation.conversation.Conversation"
        not in workspace_experience_source
    )
    assert "aware_social.social.Feed" not in workspace_experience_source
    assert "api_view workspace.control" in workspace_experience_source
    assert "api_view workspace.package_selector" in workspace_experience_source
    assert "api workspace.status.status" not in workspace_experience_source
    assert "sdk workspace_sdk.load_status" not in workspace_experience_source

    api_packages = {
        dependency["package_name"]
        for dependency in interface_toml["dependencies"]
        if dependency["kind"] == "api_package"
    }
    assert api_packages == set()


def test_repo_root_has_no_workspace_descriptor_for_node_registration() -> None:
    assert not (_REPO_ROOT / "aware.workspace.toml").exists()

    assert tuple(
        relpath
        for relpath in (
            "nodes/kernel_environment_host/aware.node.toml",
            "nodes/kernel_services_host/aware.node.toml",
            "nodes/kernel_interface_host/aware.node.toml",
            "workspaces/aware_workspace/modules/workspace/nodes/workspace_environment_host/aware.node.toml",
            "workspaces/aware_workspace/modules/workspace/nodes/workspace_services_host/aware.node.toml",
            "workspaces/aware_workspace/modules/workspace/nodes/workspace_interface_host/aware.node.toml",
        )
        if (_REPO_ROOT / relpath).is_file()
    ) == (
        "nodes/kernel_environment_host/aware.node.toml",
        "nodes/kernel_services_host/aware.node.toml",
        "nodes/kernel_interface_host/aware.node.toml",
        "workspaces/aware_workspace/modules/workspace/nodes/workspace_environment_host/aware.node.toml",
        "workspaces/aware_workspace/modules/workspace/nodes/workspace_services_host/aware.node.toml",
        "workspaces/aware_workspace/modules/workspace/nodes/workspace_interface_host/aware.node.toml",
    )
    assert not (
        _REPO_ROOT / "nodes" / "workspace_environment_host" / "aware.node.toml"
    ).exists()
    assert not (
        _REPO_ROOT / "nodes" / "workspace_services_host" / "aware.node.toml"
    ).exists()
    assert not (
        _REPO_ROOT / "nodes" / "workspace_interface_host" / "aware.node.toml"
    ).exists()
