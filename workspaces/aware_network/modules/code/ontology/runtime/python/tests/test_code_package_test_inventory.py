from __future__ import annotations

from pathlib import Path

from aware_code.package.schemas import CodePackageInfo
from aware_code.package.test_inventory import (
    build_code_package_test_inventory_for_package_info,
    build_code_package_test_inventory_from_files,
    infer_code_package_manifest_kind,
)
from aware_code.stable_ids import (
    code_package_source_config_key,
    stable_code_id,
    stable_code_package_code_id,
    stable_code_package_config_id,
    stable_code_package_id,
    stable_code_package_test_framework_id,
    stable_code_package_test_id,
    stable_code_section_id,
    stable_code_test_framework_id,
    stable_code_test_id,
    stable_code_test_unit_id,
)
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_code_ontology.code.code_section_enums import CodeSectionType


def test_infer_code_package_manifest_kind_supports_workspace_semantic_manifests() -> (
    None
):
    assert (
        infer_code_package_manifest_kind(Path("aware.environment.toml"))
        == "aware_environment_toml"
    )
    assert (
        infer_code_package_manifest_kind(Path("aware.ontology.toml"))
        == "aware_ontology_toml"
    )
    assert (
        infer_code_package_manifest_kind(Path("aware.attention.toml"))
        == "aware_attention_toml"
    )
    assert (
        infer_code_package_manifest_kind(Path("aware.pane.toml")) == "aware_pane_toml"
    )
    assert (
        infer_code_package_manifest_kind(Path("aware.node.toml")) == "aware_node_toml"
    )
    assert (
        infer_code_package_manifest_kind(Path("aware.inference.toml"))
        == "aware_inference_toml"
    )


def _source_code_package_config_id(
    *,
    manifest_kind: str,
):
    return stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind=manifest_kind,
            surface="runtime",
        ),
    )


def test_python_code_package_test_inventory_is_code_section_backed() -> None:
    inventory = build_code_package_test_inventory_from_files(
        package_name="demo-python",
        language=CodeLanguage.python,
        manifest_kind="pyproject_toml",
        manifest_relative_path="pyproject.toml",
        package_root=".",
        sources_root=".",
        manifest_text='[project]\ndependencies = ["pytest>=8"]\n',
        files={
            "tests/test_demo.py": "def test_demo():\n    assert True\n",
        },
    )

    package_id = stable_code_package_id(
        code_package_config_id=_source_code_package_config_id(
            manifest_kind="pyproject_toml",
        ),
        package_name="demo-python",
        language=CodeLanguage.python,
    )
    package_code_id = stable_code_package_code_id(
        code_package_id=package_id,
        relative_path="tests/test_demo.py",
    )
    code_id = stable_code_id(
        code_package_code_id=package_code_id,
        relative_path="tests/test_demo.py",
    )
    section_id = stable_code_section_id(
        code_id=code_id,
        section_key="test_demo",
        type=CodeSectionType.function.value,
    )
    framework_id = stable_code_test_framework_id(name="pytest")
    code_test_id = stable_code_test_id(
        code_id=code_id,
        framework_id=framework_id,
    )

    assert inventory.code_package_id == package_id
    assert len(inventory.frameworks) == 1
    assert inventory.frameworks[0].name == "pytest"
    assert inventory.frameworks[0].code_test_framework_id == framework_id
    assert inventory.frameworks[
        0
    ].code_package_test_framework_id == stable_code_package_test_framework_id(
        code_package_id=package_id,
        code_test_framework_id=framework_id,
    )
    assert len(inventory.units) == 1
    unit = inventory.units[0]
    assert unit.code_package_code_id == package_code_id
    assert unit.code_id == code_id
    assert unit.code_section_id == section_id
    assert unit.code_test_framework_id == framework_id
    assert unit.code_test_id == code_test_id
    assert unit.code_package_test_id == stable_code_package_test_id(
        code_package_id=package_id,
        code_test_id=code_test_id,
        relative_path="tests/test_demo.py",
    )
    assert unit.code_test_unit_id == stable_code_test_unit_id(
        code_test_id=code_test_id,
        code_section_id=section_id,
        unit_key="pytest:tests/test_demo.py:test_demo",
    )
    assert unit.selector == "tests/test_demo.py::test_demo"


def test_dart_code_package_test_inventory_is_code_section_backed() -> None:
    inventory = build_code_package_test_inventory_from_files(
        package_name="demo_dart",
        language=CodeLanguage.dart,
        manifest_kind="pubspec_yaml",
        manifest_relative_path="pubspec.yaml",
        package_root=".",
        sources_root="lib",
        manifest_text="dev_dependencies:\n  flutter_test:\n    sdk: flutter\n",
        files={
            "test/widget_test.dart": (
                "import 'package:flutter_test/flutter_test.dart';\n"
                "void main() {\n"
                "  testWidgets('renders home', (tester) async {});\n"
                "}\n"
            ),
        },
    )

    package_id = stable_code_package_id(
        code_package_config_id=_source_code_package_config_id(
            manifest_kind="pubspec_yaml",
        ),
        package_name="demo_dart",
        language=CodeLanguage.dart,
    )
    package_code_id = stable_code_package_code_id(
        code_package_id=package_id,
        relative_path="test/widget_test.dart",
    )
    code_id = stable_code_id(
        code_package_code_id=package_code_id,
        relative_path="test/widget_test.dart",
    )
    section_id = stable_code_section_id(
        code_id=code_id,
        section_key="main",
        type=CodeSectionType.function.value,
    )
    framework_id = stable_code_test_framework_id(name="flutter_test")
    code_test_id = stable_code_test_id(
        code_id=code_id,
        framework_id=framework_id,
    )

    assert inventory.frameworks[0].name == "flutter_test"
    assert len(inventory.units) == 1
    unit = inventory.units[0]
    assert unit.code_package_code_id == package_code_id
    assert unit.code_id == code_id
    assert unit.code_section_id == section_id
    assert unit.code_test_framework_id == framework_id
    assert unit.code_test_id == code_test_id
    assert unit.code_package_test_id == stable_code_package_test_id(
        code_package_id=package_id,
        code_test_id=code_test_id,
        relative_path="test/widget_test.dart",
    )
    assert unit.code_test_unit_id == stable_code_test_unit_id(
        code_test_id=code_test_id,
        code_section_id=section_id,
        unit_key="flutter_test:test/widget_test.dart:3:testWidgets:renders home",
    )
    assert unit.selector == "test/widget_test.dart::renders home"


def test_code_package_test_inventory_for_package_info_reads_filesystem(
    tmp_path: Path,
) -> None:
    (tmp_path / "tests").mkdir()
    _ = (tmp_path / "pyproject.toml").write_text(
        '[project]\ndependencies = ["pytest>=8"]\n',
        encoding="utf-8",
    )
    _ = (tmp_path / "tests" / "test_demo.py").write_text(
        "def test_demo():\n    assert True\n",
        encoding="utf-8",
    )

    inventory = build_code_package_test_inventory_for_package_info(
        code_package=CodePackageInfo(
            name="demo-filesystem",
            root_path=tmp_path,
            manifest_path=tmp_path / "pyproject.toml",
            language=CodeLanguage.python,
            metadata={},
        ),
        workspace_root=tmp_path,
    )

    assert inventory.manifest_kind == "pyproject_toml"
    assert inventory.manifest_relative_path == "pyproject.toml"
    assert [framework.name for framework in inventory.frameworks] == ["pytest"]
    assert [unit.selector for unit in inventory.units] == [
        "tests/test_demo.py::test_demo"
    ]
