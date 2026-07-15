from __future__ import annotations

from pathlib import Path

from aware_interface.host_runtime import resolve_interface_config_bundle
from _interface_runtime_test_paths import REPO_ROOT


def test_resolve_interface_config_bundle_selects_named_workspace_interface_when_multiple_registered(
    tmp_path: Path,
) -> None:
    repo_root = REPO_ROOT.resolve()
    runtime_manifest_path = tmp_path / "runtime" / "environment.manifest.json"
    runtime_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    default_result = resolve_interface_config_bundle(
        manifest_path=runtime_manifest_path,
        repository_root=repo_root,
    )
    selected_result = resolve_interface_config_bundle(
        manifest_path=runtime_manifest_path,
        repository_root=repo_root,
        local_interface_package_name="aware-control-interface",
    )

    assert default_result.bundle is None
    assert selected_result.source == "workspace_interface_artifact"
    assert (
        selected_result.path
        == (
            repo_root
            / "workspaces"
            / "aware_network"
            / "modules"
            / "interface"
            / "interfaces"
            / "aware_control"
            / "bundles"
            / "interface.config.bundle.json"
        ).resolve()
    )
    assert selected_result.bundle is not None
    assert selected_result.bundle.name == "aware_control"
    assert selected_result.bundle.interface_package_name == "aware-control-interface"
