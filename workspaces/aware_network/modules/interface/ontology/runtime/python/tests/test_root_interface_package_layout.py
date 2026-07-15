from __future__ import annotations

from aware_interface.workspace import InterfaceWorkspace
from aware_interface_service_dto.comms.models.interface_config_bundle import InterfaceConfigBundle
from aware_interface_ontology.stable_ids import (
    stable_interface_config_id,
    stable_interface_package_id,
)
from _interface_runtime_test_paths import REPO_ROOT


def test_root_aware_app_interface_package_loads_canonical_bundle() -> None:
    repo_root = REPO_ROOT.resolve()
    interface_toml_path = repo_root / "interfaces" / "aware_app" / "aware.interface.toml"

    snapshot = InterfaceWorkspace.from_toml(
        toml_path=interface_toml_path,
        repo_root=repo_root,
    ).build_snapshot()
    bundle = InterfaceConfigBundle.model_validate_json(
        snapshot.config_bundle_path.read_text(encoding="utf-8")
    )

    assert snapshot.repo_root == repo_root
    assert snapshot.package_root == (repo_root / "interfaces" / "aware_app").resolve()
    assert snapshot.spec_path == interface_toml_path.resolve()
    assert snapshot.spec.interface.package_name == "aware-app-interface"
    assert snapshot.spec.interface.fqn_prefix == "aware_app_interface"
    assert snapshot.config_bundle_path == (
        repo_root / "interfaces" / "aware_app" / "bundles" / "interface.config.bundle.json"
    ).resolve()

    assert bundle.interface_package_id == stable_interface_package_id(name="aware-app-interface")
    assert bundle.interface_package_name == "aware-app-interface"
    assert bundle.interface_config_id == stable_interface_config_id(name="aware-app")
    assert bundle.name == "aware-app"
    assert bundle.pane_configs == []
