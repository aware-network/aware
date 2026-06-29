from __future__ import annotations

from pathlib import Path

from aware_grammar.code_language_plugin import AWARE_CODE_PLUGIN
from aware_grammar.code_module_discovery import AwareCodeModuleDiscovery


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _create_module_fixture(
    workspace_root: Path,
    *,
    include_paths: list[str] | None = None,
) -> tuple[Path, str, str]:
    module_root = workspace_root / "modules" / "demo"
    include_paths = include_paths or ["**/*.aware"]
    include_lines = "\n".join(f'    "{pattern}",' for pattern in include_paths)

    _write(
        module_root / "aware.module.toml",
        "\n".join(
            [
                "aware = 1",
                "",
                "[[packages]]",
                'aware_toml_path = "structure/ontology/aware.toml"',
                "",
            ]
        )
        + "\n",
    )
    _write(
        module_root / "structure" / "ontology" / "aware.toml",
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
                "include_paths = [",
                include_lines,
                "]",
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
    return module_root, owned_rel_path, non_owned_rel_path


def test_aware_module_discovery_resolves_manifest_metadata(tmp_path: Path) -> None:
    discovery = AwareCodeModuleDiscovery()
    module_root, owned_rel_path, non_owned_rel_path = _create_module_fixture(tmp_path)

    module_path = module_root.relative_to(tmp_path)
    assert discovery.is_module_root(module_path, tmp_path) is True
    assert discovery.get_module_name(module_path, tmp_path) == "demo"
    assert discovery.get_entry_points(module_path, tmp_path) == []

    metadata = discovery.get_metadata(module_path, tmp_path)
    assert metadata["module_id"] == "demo"
    assert metadata["aware_module_toml_path"] == "modules/demo/aware.module.toml"
    assert metadata["structure_root"] == "modules/demo/structure"
    assert metadata["runtime_root"] == "modules/demo/runtime"
    assert metadata["representation_root"] == "modules/demo/representation"
    assert metadata["source_roots"] == ["modules/demo/structure/ontology/aware"]
    assert metadata["owned_file_paths"] == [owned_rel_path]
    assert non_owned_rel_path not in metadata["owned_file_paths"]

    packages = metadata["packages"]
    assert isinstance(packages, list)
    assert len(packages) == 1
    package = packages[0]
    assert package["aware_toml_path"] == "modules/demo/structure/ontology/aware.toml"
    assert package["package_name"] == "demo-ontology"
    assert package["package_kind"] == "ontology"
    assert package["source_root"] == "modules/demo/structure/ontology/aware"
    assert package["source_files"] == [owned_rel_path]


def test_aware_plugin_discovers_modules_from_manifest_without_file_tree(tmp_path: Path) -> None:
    module_root, owned_rel_path, non_owned_rel_path = _create_module_fixture(tmp_path)

    modules = AWARE_CODE_PLUGIN.discover_modules(file_tree={}, workspace_root=tmp_path)

    assert len(modules) == 1
    module = modules[0]
    assert module.name == "demo"
    assert module.root_path == module_root.relative_to(tmp_path)
    assert module.entry_points == []
    assert module.metadata["aware_module_toml_path"] == "modules/demo/aware.module.toml"
    assert module.metadata["owned_file_paths"] == [owned_rel_path]
    assert non_owned_rel_path not in module.metadata["owned_file_paths"]


def test_aware_module_discovery_reports_empty_owned_paths_without_fallback(tmp_path: Path) -> None:
    discovery = AwareCodeModuleDiscovery()
    module_root, _owned_rel_path, non_owned_rel_path = _create_module_fixture(
        tmp_path,
        include_paths=["apis/**/*.aware"],
    )

    module_path = module_root.relative_to(tmp_path)
    metadata = discovery.get_metadata(module_path, tmp_path)

    assert metadata["source_roots"] == ["modules/demo/structure/ontology/aware"]
    assert metadata["owned_file_paths"] == []
    assert non_owned_rel_path not in metadata["owned_file_paths"]
