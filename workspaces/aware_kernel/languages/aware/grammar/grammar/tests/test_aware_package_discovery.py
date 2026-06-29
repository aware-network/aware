from __future__ import annotations

from pathlib import Path

import pytest

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_code.module_plugin import AwareModulePlugin
from aware_code.module_plugin_registry import AwareModulePluginRegistry
from aware_code.package.semantic_contract_discovery import (
    SemanticContractCodePackageDiscovery,
)


@pytest.fixture(autouse=True)
def _register_manifest_semantic_providers() -> None:
    for provider_key, semantic_contract_module in (
        ("aware_code", "aware_code.semantic_contract"),
        ("aware_meta", "aware_meta.semantic_contract"),
        ("aware_api", "aware_api_runtime.semantic_contract"),
        ("aware_environment", "aware_environment.semantic_contract"),
        ("aware_economy", "aware_economy.semantic_contract"),
        ("aware_skill", "aware_skill.semantic_contract"),
        ("aware_sdk", "aware_sdk_runtime.semantic_contract"),
    ):
        AwareModulePluginRegistry.register(
            AwareModulePlugin(
                provider_key=provider_key,
                semantic_contract_module=semantic_contract_module,
            ),
        )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")


def _write_workspace_manifest(
    path: Path,
    *,
    handle: str = "demo",
    environments: tuple[str, ...] = (),
    apis: tuple[str, ...] = (),
    economies: tuple[str, ...] = (),
    services: tuple[str, ...] = (),
    experiences: tuple[str, ...] = (),
    panes: tuple[str, ...] = (),
    interfaces: tuple[str, ...] = (),
    nodes: tuple[str, ...] = (),
) -> tuple[Path, str]:
    def _toml_array(values: tuple[str, ...]) -> str:
        return "[" + ", ".join(f'"{value}"' for value in values) + "]"

    doc_path = path / "aware.workspace.toml"
    doc_text = (
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                f'handle = "{handle}"',
                f"environments = {_toml_array(environments)}",
                f"apis = {_toml_array(apis)}",
                f"economies = {_toml_array(economies)}",
                f"services = {_toml_array(services)}",
                f"experiences = {_toml_array(experiences)}",
                f"panes = {_toml_array(panes)}",
                f"interfaces = {_toml_array(interfaces)}",
                f"nodes = {_toml_array(nodes)}",
                "",
            ]
        )
        + "\n"
    )
    _write(doc_path, doc_text)
    return doc_path, doc_text


def _create_package_fixture(workspace_root: Path) -> tuple[Path, str, str]:
    package_root = workspace_root / "modules" / "demo" / "structure" / "ontology"
    _write(
        package_root / "aware.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[package]",
                'package_name = "demo-ontology"',
                'fqn_prefix = "aware_demo"',
                'kind = "ontology"',
                "",
                "[build]",
                'environment_slug = "aware_demo"',
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        )
        + "\n",
    )

    owned_rel_path = "modules/demo/structure/ontology/aware/demo/demo_root.aware"
    non_owned_rel_path = "modules/demo/programs/demo_seed.aware"
    _write(
        workspace_root / owned_rel_path,
        "class DemoRoot {\n    name String\n}\n",
    )
    _write(
        workspace_root / non_owned_rel_path,
        "class DemoSeed {\n    title String\n}\n",
    )
    return package_root, owned_rel_path, non_owned_rel_path


def _create_api_package_fixture(workspace_root: Path) -> tuple[Path, str]:
    package_root = workspace_root / "modules" / "demo" / "apis" / "public_api"
    _write(
        package_root / "aware.api.toml",
        "\n".join(
            [
                "aware_api = 1",
                "",
                "[api]",
                'package_name = "demo-api"',
                'fqn_prefix = "aware_demo_api"',
                "",
                "[build]",
                'sources_dir = "apis"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        )
        + "\n",
    )
    owned_rel_path = "modules/demo/apis/public_api/apis/demo/demo_api.aware"
    _write(
        workspace_root / owned_rel_path,
        "class DemoApi {\n    name String\n}\n",
    )
    return package_root, owned_rel_path


def _create_economy_package_fixture(workspace_root: Path) -> tuple[Path, str]:
    package_root = workspace_root / "modules" / "demo" / "economy" / "workspace_pricing"
    _write(
        package_root / "aware.economy.toml",
        "\n".join(
            [
                "aware_economy = 1",
                "",
                "[economy]",
                'package_name = "demo-economy"',
                'fqn_prefix = "aware_demo_economy"',
                "",
                "[build]",
                'sources_dir = "economy"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        )
        + "\n",
    )
    owned_rel_path = "modules/demo/economy/workspace_pricing/economy/demo/root.aware"
    _write(
        workspace_root / owned_rel_path,
        "class DemoEconomyRoot {\n    name String\n}\n",
    )
    return package_root, owned_rel_path


def _create_skill_package_fixture(workspace_root: Path) -> tuple[Path, str]:
    package_root = workspace_root / "modules" / "demo" / "skills" / "door_control"
    _write(
        package_root / "aware.skill.toml",
        "\n".join(
            [
                "aware_skill = 1",
                "",
                "[skill]",
                'package_name = "demo-skill"',
                'fqn_prefix = "demo_skill"',
                "",
                "[build]",
                'sources_dir = "skills"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        )
        + "\n",
    )
    owned_rel_path = "modules/demo/skills/door_control/skills/demo/door_control.aware"
    _write(
        workspace_root / owned_rel_path,
        "skill door_control {\n    api home_devices;\n}\n",
    )
    return package_root, owned_rel_path


def _create_sdk_package_fixture(workspace_root: Path) -> tuple[Path, str]:
    package_root = workspace_root / "modules" / "demo" / "sdks" / "control_sdk"
    _write(
        package_root / "aware.sdk.toml",
        "\n".join(
            [
                "aware_sdk = 1",
                "",
                "[sdk]",
                'package_name = "demo-sdk"',
                'fqn_prefix = "demo_sdk"',
                "",
                "[build]",
                'sources_dir = "sdks"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        )
        + "\n",
    )
    owned_rel_path = "modules/demo/sdks/control_sdk/sdks/demo/control_sdk.aware"
    _write(
        workspace_root / owned_rel_path,
        "sdk control_sdk {\n    api home_devices;\n    operation status {\n        endpoint home_devices.status.get;\n    }\n}\n",
    )
    return package_root, owned_rel_path


def _create_environment_profile_package_fixture(
    workspace_root: Path,
) -> tuple[Path, str]:
    package_root = workspace_root / "environment" / "profiles" / "control"
    _write(
        package_root / "aware.environment.profile.toml",
        "\n".join(
            [
                "aware_environment_profile = 1",
                "",
                "[environment_profile]",
                'package_name = "aware-control-environment-profile"',
                'profile_key = "control.default"',
                'environment_handle = "kernel"',
                "version_number = 1",
                'title = "Aware Control"',
                "",
                "[build]",
                'sources_dir = "aware"',
                'include_paths = ["**/*.aware"]',
                "exclude_paths = []",
                "",
            ]
        )
        + "\n",
    )
    owned_rel_path = "environment/profiles/control/aware/control.aware"
    _write(
        workspace_root / owned_rel_path,
        'environment_profile control.default {\n    title "Aware Control"\n}\n',
    )
    return package_root, owned_rel_path


def test_aware_package_discovery_resolves_manifest_metadata(tmp_path: Path) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    package_root, owned_rel_path, non_owned_rel_path = _create_package_fixture(tmp_path)
    owned_file_path = tmp_path / owned_rel_path

    package_path = package_root.relative_to(tmp_path)
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert discovery.get_package_name(package_path, tmp_path) == "demo-ontology"
    assert discovery.get_manifest_path(package_path, tmp_path) == Path(
        "modules/demo/structure/ontology/aware.toml"
    )
    resolution = discovery.resolve_package_for_path(
        path=owned_file_path, workspace_root=tmp_path
    )
    assert resolution.document_path == Path(owned_rel_path)
    assert resolution.nearest_package_root == Path("modules/demo/structure/ontology")
    assert resolution.nearest_manifest_path == Path(
        "modules/demo/structure/ontology/aware.toml"
    )
    assert resolution.nearest_manifest_declared_in_workspace is None
    assert resolution.owning_package_root == Path("modules/demo/structure/ontology")
    assert resolution.owning_manifest_path == Path(
        "modules/demo/structure/ontology/aware.toml"
    )
    assert resolution.authoritative_workspace_root is None
    assert resolution.authoritative_workspace_manifest_path is None
    assert resolution.workspace_membership_required is False

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["manifest_kind"] == "aware_toml"
    assert metadata["aware_toml_path"] == "modules/demo/structure/ontology/aware.toml"
    assert metadata["package_root"] == "modules/demo/structure/ontology"
    assert metadata["package_kind"] == "ontology"
    assert metadata["fqn_prefix"] == "aware_demo"
    assert metadata["source_root"] == "modules/demo/structure/ontology/aware"
    metadata_owned_paths = metadata["owned_file_paths"]
    assert isinstance(metadata_owned_paths, list)
    assert metadata_owned_paths == [owned_rel_path]
    assert non_owned_rel_path not in metadata_owned_paths


def test_aware_plugin_discovers_packages_from_manifest_without_file_tree(
    tmp_path: Path,
) -> None:
    package_root, owned_rel_path, non_owned_rel_path = _create_package_fixture(tmp_path)

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-ontology"
    assert package.root_path == package_root.relative_to(tmp_path)
    assert package.manifest_path == Path("modules/demo/structure/ontology/aware.toml")
    owned_file_paths = package.metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]
    assert non_owned_rel_path not in owned_file_paths


def test_aware_package_discovery_stays_distinct_from_module_discovery(
    tmp_path: Path,
) -> None:
    _package_root, _owned_rel_path, _non_owned_rel_path = _create_package_fixture(
        tmp_path
    )

    modules = AWARE_CODE_PLUGIN.discover_modules(file_tree={}, workspace_root=tmp_path)
    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert modules == []
    assert len(packages) == 1


def test_aware_package_discovery_resolves_api_manifest_metadata(tmp_path: Path) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    package_root, owned_rel_path = _create_api_package_fixture(tmp_path)

    package_path = package_root.relative_to(tmp_path)
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert discovery.get_package_name(package_path, tmp_path) == "demo-api"
    assert discovery.get_manifest_path(package_path, tmp_path) == Path(
        "modules/demo/apis/public_api/aware.api.toml"
    )

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["manifest_kind"] == "aware_api_toml"
    assert metadata["authored_manifest_kind"] == "aware_api_toml"
    assert (
        metadata["aware_api_toml_path"] == "modules/demo/apis/public_api/aware.api.toml"
    )
    assert metadata["package_root"] == "modules/demo/apis/public_api"
    assert metadata["package_kind"] == "api"
    assert metadata["fqn_prefix"] == "aware_demo_api"
    assert metadata["source_root"] == "modules/demo/apis/public_api/apis"
    metadata_owned_paths = metadata["owned_file_paths"]
    assert isinstance(metadata_owned_paths, list)
    assert metadata_owned_paths == [owned_rel_path]


def test_aware_plugin_discovers_api_manifest_without_file_tree(tmp_path: Path) -> None:
    package_root, owned_rel_path = _create_api_package_fixture(tmp_path)

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-api"
    assert package.root_path == package_root.relative_to(tmp_path)
    assert package.manifest_path == Path("modules/demo/apis/public_api/aware.api.toml")
    assert package.metadata["manifest_kind"] == "aware_api_toml"
    assert package.metadata["authored_manifest_kind"] == "aware_api_toml"
    owned_file_paths = package.metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_package_discovery_resolves_environment_profile_manifest_metadata(
    tmp_path: Path,
) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    package_root, owned_rel_path = _create_environment_profile_package_fixture(tmp_path)

    package_path = package_root.relative_to(tmp_path)
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert (
        discovery.get_package_name(package_path, tmp_path)
        == "aware-control-environment-profile"
    )
    assert discovery.get_manifest_path(package_path, tmp_path) == Path(
        "environment/profiles/control/aware.environment.profile.toml"
    )

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["manifest_kind"] == "aware_environment_profile_toml"
    assert metadata["authored_manifest_kind"] == "aware_environment_profile_toml"
    assert (
        metadata["aware_environment_profile_toml_path"]
        == "environment/profiles/control/aware.environment.profile.toml"
    )
    assert metadata["package_root"] == "environment/profiles/control"
    assert metadata["package_kind"] == "environment_profile"
    assert metadata["environment_handle"] == "kernel"
    assert metadata["profile_key"] == "control.default"
    assert metadata["source_root"] == "environment/profiles/control/aware"
    owned_file_paths = metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_package_discovery_resolves_economy_manifest_metadata(
    tmp_path: Path,
) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    package_root, owned_rel_path = _create_economy_package_fixture(tmp_path)

    package_path = package_root.relative_to(tmp_path)
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert discovery.get_package_name(package_path, tmp_path) == "demo-economy"
    assert discovery.get_manifest_path(package_path, tmp_path) == Path(
        "modules/demo/economy/workspace_pricing/aware.economy.toml"
    )

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["manifest_kind"] == "aware_economy_toml"
    assert metadata["authored_manifest_kind"] == "aware_economy_toml"
    assert (
        metadata["aware_economy_toml_path"]
        == "modules/demo/economy/workspace_pricing/aware.economy.toml"
    )
    assert metadata["package_root"] == "modules/demo/economy/workspace_pricing"
    assert metadata["package_kind"] == "economy"
    assert metadata["fqn_prefix"] == "aware_demo_economy"
    assert metadata["source_root"] == "modules/demo/economy/workspace_pricing/economy"
    owned_file_paths = metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_plugin_discovers_economy_manifest_without_file_tree(
    tmp_path: Path,
) -> None:
    package_root, owned_rel_path = _create_economy_package_fixture(tmp_path)

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-economy"
    assert package.root_path == package_root.relative_to(tmp_path)
    assert package.manifest_path == Path(
        "modules/demo/economy/workspace_pricing/aware.economy.toml"
    )
    assert package.metadata["manifest_kind"] == "aware_economy_toml"
    assert package.metadata["authored_manifest_kind"] == "aware_economy_toml"
    owned_file_paths = package.metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_package_discovery_resolves_skill_manifest_metadata(
    tmp_path: Path,
) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    package_root, owned_rel_path = _create_skill_package_fixture(tmp_path)

    package_path = package_root.relative_to(tmp_path)
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert discovery.get_package_name(package_path, tmp_path) == "demo-skill"
    assert discovery.get_manifest_path(package_path, tmp_path) == Path(
        "modules/demo/skills/door_control/aware.skill.toml"
    )

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["manifest_kind"] == "aware_skill_toml"
    assert metadata["authored_manifest_kind"] == "aware_skill_toml"
    assert (
        metadata["aware_skill_toml_path"]
        == "modules/demo/skills/door_control/aware.skill.toml"
    )
    assert metadata["package_root"] == "modules/demo/skills/door_control"
    assert metadata["package_kind"] == "skill"
    assert metadata["fqn_prefix"] == "demo_skill"
    assert metadata["source_root"] == "modules/demo/skills/door_control/skills"
    owned_file_paths = metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_plugin_discovers_skill_manifest_without_file_tree(
    tmp_path: Path,
) -> None:
    package_root, owned_rel_path = _create_skill_package_fixture(tmp_path)

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-skill"
    assert package.root_path == package_root.relative_to(tmp_path)
    assert package.manifest_path == Path(
        "modules/demo/skills/door_control/aware.skill.toml"
    )
    assert package.metadata["manifest_kind"] == "aware_skill_toml"
    assert package.metadata["authored_manifest_kind"] == "aware_skill_toml"
    owned_file_paths = package.metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_package_discovery_resolves_sdk_manifest_metadata(tmp_path: Path) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    package_root, owned_rel_path = _create_sdk_package_fixture(tmp_path)

    package_path = package_root.relative_to(tmp_path)
    assert discovery.is_package_root(package_path, tmp_path) is True
    assert discovery.get_package_name(package_path, tmp_path) == "demo-sdk"
    assert discovery.get_manifest_path(package_path, tmp_path) == Path(
        "modules/demo/sdks/control_sdk/aware.sdk.toml"
    )

    metadata = discovery.get_metadata(package_path, tmp_path)
    assert metadata["manifest_kind"] == "aware_sdk_toml"
    assert metadata["authored_manifest_kind"] == "aware_sdk_toml"
    assert (
        metadata["aware_sdk_toml_path"]
        == "modules/demo/sdks/control_sdk/aware.sdk.toml"
    )
    assert metadata["package_root"] == "modules/demo/sdks/control_sdk"
    assert metadata["package_kind"] == "sdk"
    assert metadata["fqn_prefix"] == "demo_sdk"
    assert metadata["source_root"] == "modules/demo/sdks/control_sdk/sdks"
    owned_file_paths = metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_plugin_discovers_sdk_manifest_without_file_tree(tmp_path: Path) -> None:
    package_root, owned_rel_path = _create_sdk_package_fixture(tmp_path)

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-sdk"
    assert package.root_path == package_root.relative_to(tmp_path)
    assert package.manifest_path == Path("modules/demo/sdks/control_sdk/aware.sdk.toml")
    assert package.metadata["manifest_kind"] == "aware_sdk_toml"
    assert package.metadata["authored_manifest_kind"] == "aware_sdk_toml"
    owned_file_paths = package.metadata["owned_file_paths"]
    assert isinstance(owned_file_paths, list)
    assert owned_file_paths == [owned_rel_path]


def test_aware_package_discovery_fails_closed_for_undeclared_nested_workspace_package(
    tmp_path: Path,
) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    workspace_root = tmp_path / "products" / "home_workspace"
    declared_api_root, _declared_owned_rel_path = _create_api_package_fixture(
        workspace_root
    )
    undeclared_package_root, owned_rel_path, _non_owned_rel_path = (
        _create_package_fixture(workspace_root)
    )
    _write_workspace_manifest(
        workspace_root,
        apis=("modules/demo/apis/public_api/aware.api.toml",),
        interfaces=(),
    )

    owned_file_path = workspace_root / owned_rel_path
    resolution = discovery.resolve_package_for_path(
        path=owned_file_path, workspace_root=tmp_path
    )
    assert resolution.document_path == Path(f"products/home_workspace/{owned_rel_path}")
    assert resolution.nearest_package_root == Path(
        "products/home_workspace/modules/demo/structure/ontology"
    )
    assert resolution.nearest_manifest_path == Path(
        "products/home_workspace/modules/demo/structure/ontology/aware.toml"
    )
    assert resolution.nearest_manifest_declared_in_workspace is False
    assert resolution.owning_package_root is None
    assert resolution.owning_manifest_path is None
    assert resolution.authoritative_workspace_root == Path("products/home_workspace")
    assert resolution.authoritative_workspace_manifest_path == Path(
        "products/home_workspace/aware.workspace.toml"
    )
    assert resolution.workspace_membership_required is True
    assert (
        discovery.is_package_root(
            undeclared_package_root.relative_to(tmp_path), tmp_path
        )
        is False
    )

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-api"
    assert package.root_path == declared_api_root.relative_to(tmp_path)
    assert package.manifest_path == Path(
        "products/home_workspace/modules/demo/apis/public_api/aware.api.toml"
    )


def test_aware_package_discovery_accepts_workspace_module_package_membership(
    tmp_path: Path,
) -> None:
    discovery = SemanticContractCodePackageDiscovery()
    workspace_root = tmp_path / "products" / "home_workspace"
    package_root, owned_rel_path, _non_owned_rel_path = _create_package_fixture(
        workspace_root
    )
    _write(
        workspace_root / "modules" / "demo" / "aware.module.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'id = "ontology"',
                'kind = "ontology"',
                'manifest = "structure/ontology/aware.toml"',
                'visibility = "module"',
                "",
            ]
        )
        + "\n",
    )
    _write(
        workspace_root / "aware.workspace.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[workspace]",
                'handle = "home_workspace"',
                "environments = []",
                "apis = []",
                "economies = []",
                "services = []",
                "experiences = []",
                "panes = []",
                "interfaces = []",
                "nodes = []",
                "",
                "[[workspace.modules]]",
                'id = "demo"',
                'path = "modules/demo"',
                "",
            ]
        )
        + "\n",
    )

    owned_file_path = workspace_root / owned_rel_path
    resolution = discovery.resolve_package_for_path(
        path=owned_file_path,
        workspace_root=tmp_path,
    )

    assert resolution.document_path == Path(f"products/home_workspace/{owned_rel_path}")
    assert resolution.nearest_manifest_declared_in_workspace is True
    assert resolution.owning_package_root == Path(
        "products/home_workspace/modules/demo/structure/ontology"
    )
    assert resolution.owning_manifest_path == Path(
        "products/home_workspace/modules/demo/structure/ontology/aware.toml"
    )
    assert (
        discovery.is_package_root(package_root.relative_to(tmp_path), tmp_path) is True
    )

    packages = AWARE_CODE_PLUGIN.discover_packages(
        file_tree={}, workspace_root=tmp_path
    )

    assert len(packages) == 1
    package = packages[0]
    assert package.name == "demo-ontology"
    assert package.root_path == package_root.relative_to(tmp_path)
